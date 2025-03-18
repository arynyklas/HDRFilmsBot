from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from httpx import AsyncClient
from contextlib import suppress
from pathlib import Path

import sqlalchemy as sa
import re
import asyncio
import os
import struct

from src import db, models, utils
from src.cache import AsyncTimedRezkaCacheData
from src.basic_data import TEXTS
from src.config import config


SLEEP_TIME = 3.
DOWNLOAD_EDIT_PROGRESS_DELAY = 1.5
FILE_NAME_CONSTUCTOR = "item_{}_{}.mp4"
FILE_CHECK_RESOLUTION_MAX_READ_SIZE = 1024 * 1024 * 1  # 1 MB

http_client = AsyncClient(
    follow_redirects = True
)


WGET_PROGRESS_PATTERN = re.compile(r"(\d+)%")


def parse_mp4_atom(data: bytes, offset: int, size: int) -> tuple[str, bytes, int]:
    if offset + 8 > size:
        raise ValueError("Atom size is less than 8 bytes")

    atom_size = struct.unpack(">I", data[offset:offset + 4])[0]
    atom_type = data[offset + 4:offset + 8].decode("ascii")

    if atom_size > 8:
        atom_data = data[offset + 8:offset + atom_size]
    else:
        atom_data = b""

    return (atom_type, atom_data, atom_size)

def find_resolution_in_moov(data: bytes, size: int) -> tuple[int, int] | tuple[None, None]:
    offset = 0

    while offset < size:
        try:
            atom_type, atom_data, atom_size = parse_mp4_atom(data, offset, size)

        except ValueError:
            break

        if atom_type == "moov":
            moov_offset = 0

            while moov_offset < len(atom_data):
                trak_type, trak_data, trak_size = parse_mp4_atom(atom_data, moov_offset, len(atom_data))

                if trak_type == "trak":
                    trak_offset = 0

                    while trak_offset < len(trak_data):
                        tkhd_type, tkhd_data, tkhd_size = parse_mp4_atom(trak_data, trak_offset, len(trak_data))

                        if tkhd_type == "tkhd":
                            if len(tkhd_data) >= 84: 
                                width = struct.unpack(">I", tkhd_data[76:80])[0] >> 16  
                                height = struct.unpack(">I", tkhd_data[80:84])[0] >> 16 

                                return (width, height)

                        trak_offset += tkhd_size

                moov_offset += trak_size

        offset += atom_size

    return (None, None)


async def determine_content_length_by_url(url: str) -> int:
    response = await http_client.head(url)

    return int(response.headers["Content-Length"])


async def _edit_users_message(bot: Bot, db_download_item_queue: db.DownloadItemQueue, text: str) -> None:
    for user_tg_id, user_tg_message_id in zip(db_download_item_queue.user_tg_ids, db_download_item_queue.user_tg_message_ids):
        with suppress(TelegramAPIError):
            await bot.edit_message_text(
                chat_id = user_tg_id,
                message_id = user_tg_message_id,
                text = text
            )

        await asyncio.sleep(config.download_items_queue_per_message_delay)


def determine_content_resolution_by_file_content(file_path: Path) -> tuple[int, int] | tuple[None, None]:
    with file_path.open("rb") as file:
        data = file.read(FILE_CHECK_RESOLUTION_MAX_READ_SIZE)

    return find_resolution_in_moov(data, len(data))


async def _db_session_worker(
    bot: Bot,
    db_session: db.DBSession,
    rezka_cache_data: AsyncTimedRezkaCacheData
) -> None:
    db_download_item_queue = (await db_session.execute(
        sa.select(db.DownloadItemQueue)
        .limit(1)
    )).scalars().first()

    if db_download_item_queue is None:
        return

    cache_rezka_data_key = models.CachedRezkaData.get_key(
        item_id = db_download_item_queue.item_id,
        translator_id = db_download_item_queue.translator_id,
        season_id = db_download_item_queue.season_id,
        episode_id = db_download_item_queue.episode_id
    )

    got_cached_rezka_data = await rezka_cache_data.get_or_set(
        item_id = db_download_item_queue.item_id,
        item_title = db_download_item_queue.item_title,
        translator_id = db_download_item_queue.translator_id,
        translator_title = db_download_item_queue.translator_title,
        translator_additional_arguments = db_download_item_queue.translator_additional_arguments,
        is_film = db_download_item_queue.is_film,
        season_id = db_download_item_queue.season_id,
        episode_id = db_download_item_queue.episode_id
    )

    selected_quality: str | None = None
    selected_direct_url: str | None = None

    if not got_cached_rezka_data.urls:
        await db_session.delete(db_download_item_queue)

        await _edit_users_message(
            bot = bot,
            db_download_item_queue = db_download_item_queue,
            text = TEXTS.not_avaliable.default
        )

        return

    for quality, direct_url in reversed(got_cached_rezka_data.urls.items()):
        if await determine_content_length_by_url(direct_url) < config.max_file_upload_size:
            selected_quality = quality
            selected_direct_url = direct_url

            break

    if not selected_quality or not selected_direct_url:
        await db_session.delete(db_download_item_queue)

        await _edit_users_message(
            bot = bot,
            db_download_item_queue = db_download_item_queue,
            text = TEXTS.not_avaliable.default
        )

        return

    await _edit_users_message(
        bot = bot,
        db_download_item_queue = db_download_item_queue,
        text = TEXTS.select.download_quality_statuses.downloading.format(
            quality = selected_quality,
            progress_percentage = 0
        )
    )

    file_name = FILE_NAME_CONSTUCTOR.format(
        cache_rezka_data_key,
        selected_quality.replace(" ", "-")
    )

    save_path = config.downloads_temp_dirpath / file_name

    process = await asyncio.create_subprocess_exec(
        "wget",
        selected_direct_url,
        "-O", save_path.resolve().as_posix(),
        "--progress=dot:giga",
        stdout = asyncio.subprocess.PIPE,
        stderr = asyncio.subprocess.PIPE
    )

    last_update_time = utils.get_timestamp_float()

    async for line in process.stderr:  # type: ignore
        match = WGET_PROGRESS_PATTERN.search(line.decode())

        if match:
            progress = int(match.group(1))

            if utils.get_timestamp_float() - last_update_time >= DOWNLOAD_EDIT_PROGRESS_DELAY:
                await _edit_users_message(
                    bot = bot,
                    db_download_item_queue = db_download_item_queue,
                    text = TEXTS.select.download_quality_statuses.downloading.format(
                        quality = selected_quality,
                        progress_percentage = progress
                    )
                )

                last_update_time = utils.get_timestamp_float()

    await process.wait()

    if process.returncode != 0:
        stderr = await process.stderr.read()  # type: ignore

        raise Exception(stderr.decode())

    await _edit_users_message(
        bot = bot,
        db_download_item_queue = db_download_item_queue,
        text = TEXTS.select.download_quality_statuses.uploading.format(
            quality = selected_quality
        )
    )

    width, height = determine_content_resolution_by_file_content(save_path)

    bot_video_message = await bot.send_video(
        chat_id = config.download_items_queue_to_chat_id,
        video = f"file://{save_path.resolve()}",
        width = width,
        height = height,
        caption = "{}\n{}\n{}{}".format(
            db_download_item_queue.item_title,
            db_download_item_queue.translator_title,
            selected_quality,
            (
                "\ns{}e{}".format(
                    db_download_item_queue.season_id,
                    db_download_item_queue.episode_id
                )
                if db_download_item_queue.season_id and db_download_item_queue.episode_id
                else
                ""
            )
        )
    )

    video_file_id = bot_video_message.video.file_id  # type: ignore

    db_downloaded_item = db.DownloadedItem(
        item_id = db_download_item_queue.item_id,
        item_title = db_download_item_queue.item_title,
        translator_id = db_download_item_queue.translator_id,
        translator_title = db_download_item_queue.translator_title,
        translator_additional_arguments = db_download_item_queue.translator_additional_arguments,
        is_film = db_download_item_queue.is_film,
        season_id = db_download_item_queue.season_id,
        episode_id = db_download_item_queue.episode_id,
        quality = selected_quality,
        video_file_id = video_file_id
    )

    db_session.add(db_downloaded_item)
    await db_session.delete(db_download_item_queue)

    os.remove(save_path)

    message_caption = TEXTS.select.download_quality_statuses.caption.default.format(
        item_title = db_downloaded_item.item_title,
        series_text = (
            TEXTS.select.download_quality_statuses.caption.series_test.format(
                season_id = db_downloaded_item.season_id,
                episode_id = db_downloaded_item.episode_id
            )
            if db_downloaded_item.season_id and db_downloaded_item.episode_id
            else
            ""
        ),
        translator = db_downloaded_item.translator_title,
        quality = db_downloaded_item.quality
    )

    for user_tg_id, user_tg_message_id, user_tg_reply_message_id in zip(db_download_item_queue.user_tg_ids, db_download_item_queue.user_tg_message_ids, db_download_item_queue.user_tg_reply_message_ids):
        with suppress(TelegramAPIError):
            await bot.delete_message(
                chat_id = user_tg_id,
                message_id = user_tg_message_id
            )

            await asyncio.sleep(config.download_items_queue_per_message_delay)

            await bot.send_video(
                chat_id = user_tg_id,
                video = video_file_id,
                caption = message_caption,
                reply_to_message_id = user_tg_reply_message_id,
                protect_content = True
            )

        await asyncio.sleep(config.download_items_queue_per_message_delay)


async def download_items_queue_worker(
    bot: Bot,
    db_sessionmaker: db.DBSessionMaker,
    rezka_cache_data: AsyncTimedRezkaCacheData
) -> None:
    if not config.downloads_temp_dirpath.exists():
        config.downloads_temp_dirpath.mkdir()

    while True:
        async with db_sessionmaker() as db_session:
            await _db_session_worker(
                bot = bot,
                db_session = db_session,
                rezka_cache_data = rezka_cache_data
            )

            await db_session.commit()

        await asyncio.sleep(SLEEP_TIME)
