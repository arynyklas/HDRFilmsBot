from aiogram import Router, types, Bot, enums as aiogram_enums

import sqlalchemy as sa

from src import db, utils, keyboards
from src.cache import AsyncTimedRezkaCacheShortInfo
from src.basic_data import TEXTS
from .start import start_command_handler


short_info_router = Router()


def _short_info_value_or_none(key: str, format_value: str | None) -> str:
    if not format_value:
        return ""

    return TEXTS.short_info.attrs.get(key, "").format(format_value)


@short_info_router.message()
async def via_bot_message_handler(
    message: types.Message,
    db_user: db.User,
    bot: Bot,
    rezka_cache_short_info: AsyncTimedRezkaCacheShortInfo,
    db_session: db.DBSession
) -> None:
    if not message.via_bot or message.content_type != aiogram_enums.ContentType.TEXT or message.via_bot.username != (await bot.me()).username:
        await start_command_handler(
            message = message
        )

        return

    _, url = utils.parse_item_message(message)

    short_info, translators = await rezka_cache_short_info.get_or_set(url)

    item_id = utils.rezka_extract_id_from_url(url)

    track_series = (await db_session.execute(
        sa.select(db.TrackSeries)
        .where(
            db.TrackSeries.item_id == item_id
        )
    )).scalar()

    track_series_users_count = (
        len(track_series.user_tg_ids)
        if track_series
        else
        0
    )

    await message.reply(
        text = TEXTS.short_info.default.format(
            title = short_info.title,
            ratings = "\n".join([
                TEXTS.short_info.rating_attr.format(
                    source = rating.source,
                    rating = rating.rating
                )
                for rating in short_info.ratings
            ]),
            track_series_text = (
                (
                    (
                        TEXTS.short_info.track_series.with_user_more.format(
                            users_count = track_series_users_count - 1
                        )
                        if track_series_users_count > 1
                        else
                        TEXTS.short_info.track_series.with_user_alone
                    )
                    if await db.utils.user_tracking_series(
                        item_id = item_id,
                        user_tg_id = db_user.tg_id,
                        db_session = db_session
                    )
                    else
                    TEXTS.short_info.track_series.without_user.format(
                        users_count = track_series_users_count
                    )
                )
                if track_series_users_count > 0
                else
                ""
            ),
            **{
                field_name: _short_info_value_or_none(
                    key = field_name,
                    format_value = getattr(short_info, field_name)
                )
                for field_name in short_info.OPTIONAL_STRING_FIELDS_NAMES
            }
        )
    )

    if short_info.is_film is None or not translators:
        await message.reply(
            text = TEXTS.not_avaliable.default
        )

        return

    await message.reply(
        text = TEXTS.select.translator,
        reply_markup = keyboards.translators(
            item_id = item_id,
            is_film = short_info.is_film,
            translators = translators
        )
    )
