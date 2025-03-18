from aiogram import Bot
from rezka_api_sdk import RezkaAPIException
from aiogram.exceptions import TelegramAPIError

import sqlalchemy as sa
import asyncio
import typing

from src import db, utils
from src.cache import AsyncTimedRezkaCacheData
from src.basic_data import TEXTS
from src.config import config


FETCH_LIMIT = 100


async def _get_track_series_by_cursor(session: db.DBSession, last_id: int | None = None) -> tuple[typing.Sequence[db.TrackSeries], bool]:
    query = sa.select(db.TrackSeries)

    if last_id:
        query = query.where(db.TrackSeries.id > last_id)

    query = (
        query
        .order_by(db.TrackSeries.id.asc())
        .limit(FETCH_LIMIT + 1)
    )

    results = (await session.execute(query)).scalars().all()

    has_next = len(results) > FETCH_LIMIT

    if has_next:
        results = results[:FETCH_LIMIT]

    return (results, has_next)


async def db_track_series_checker(
    bot: Bot,
    db_sessionmaker: db.DBSessionMaker,
    rezka_cache_data: AsyncTimedRezkaCacheData,
    logger: utils.Logger
) -> None:
    while True:
        await asyncio.sleep(config.track_series_checker_delay)

        last_track_series_id: int | None = None
        has_next = True
        notify_updates: list[tuple[str, list[str], list[int], list[int]]] = []

        async with db_sessionmaker() as db_session:
            await db_session.execute(
                sa.delete(db.TrackSeries).where(
                    sa.func.cardinality(db.TrackSeries.user_tg_ids) == 0
                )
            )

            unnest_ids_cte = (
                sa.select(
                    db.TrackSeries.id.label("ts_id"),
                    db.TrackSeries.item_id,
                    db.TrackSeries.translator_id,
                    sa.func.unnest(db.TrackSeries.user_tg_ids).label("uid")
                )
                .cte("unnest_ids_cte")
            )

            unnest_msgs_cte = (
                sa.select(
                    db.TrackSeries.id.label("ts_id"),
                    db.TrackSeries.item_id,
                    db.TrackSeries.translator_id,
                    sa.func.unnest(db.TrackSeries.user_tg_message_ids).label("mid")
                )
                .cte("unnest_msgs_cte")
            )

            merge_cte = (
                sa.select(
                    db.TrackSeries.item_id,
                    db.TrackSeries.translator_id,
                    sa.func.min(db.TrackSeries.id).label("min_id"),
                    sa.func.array_agg(sa.distinct(unnest_ids_cte.c.uid)).label("merged_user_tg_ids"),
                    sa.func.array_agg(sa.distinct(unnest_msgs_cte.c.mid)).label("merged_user_tg_message_ids")
                )
                .select_from(db.TrackSeries)
                .join(
                    unnest_ids_cte,
                    unnest_ids_cte.c.ts_id == db.TrackSeries.id
                )
                .join(
                    unnest_msgs_cte,
                    unnest_msgs_cte.c.ts_id == db.TrackSeries.id
                )
                .group_by(
                    db.TrackSeries.item_id,
                    db.TrackSeries.translator_id
                )
                .having(sa.func.count(sa.distinct(db.TrackSeries.id)) > 1)
                .cte("merge_cte")
            )

            update_stmt = (
                sa.update(db.TrackSeries)
                .where(db.TrackSeries.id == merge_cte.c.min_id)
                .values(
                    user_tg_ids = merge_cte.c.merged_user_tg_ids,
                    user_tg_message_ids = merge_cte.c.merged_user_tg_message_ids
                )
                .execution_options(synchronize_session=False)
                .add_cte(merge_cte)
            )

            delete_stmt = (
                sa.delete(db.TrackSeries)
                .where(
                    db.TrackSeries.item_id == merge_cte.c.item_id,
                    db.TrackSeries.translator_id == merge_cte.c.translator_id,
                    db.TrackSeries.id != merge_cte.c.min_id
                )
                .execution_options(synchronize_session=False)
                .add_cte(merge_cte)
            )

            await db_session.execute(update_stmt)
            await db_session.execute(delete_stmt)

            await db_session.commit()

            while has_next:
                db_track_series_list, has_next = await _get_track_series_by_cursor(
                    session = db_session,
                    last_id = last_track_series_id
                )

                for db_track_series in db_track_series_list:
                    item_id = db_track_series.item_id
                    translator_id = db_track_series.translator_id
                    translator_additional_arguments = db_track_series.translator_additional_arguments
                    last_season_id = db_track_series.last_season_id
                    last_episode_id = db_track_series.last_episode_id

                    logger.info(f"Checking track series: {item_id=}, {translator_id=}, {translator_additional_arguments=}, {last_season_id=}, {last_episode_id=}")

                    try:
                        got_cached_rezka_data = await rezka_cache_data.get_or_set(
                            item_id = item_id,
                            item_title = db_track_series.item_title,
                            translator_id = translator_id,
                            translator_title = db_track_series.translator_title,
                            translator_additional_arguments = translator_additional_arguments,
                            is_film = False
                        )

                    except RezkaAPIException as ex:
                        if ex.description and "premium content" in ex.description.lower():
                            await asyncio.sleep(config.track_series_checker_per_delay)

                            continue

                        logger.exception(
                            msg = "Error while getting direct urls",
                            exc_info = ex,
                            extra = dict(
                                document_name = f"track-{item_id}-{translator_id}-{utils.get_timestamp_int()}"
                            )
                        )

                        await asyncio.sleep(config.track_series_checker_per_delay)

                        continue

                    if got_cached_rezka_data.seasons and got_cached_rezka_data.episodes:
                        if not last_season_id or not last_episode_id:
                            db_track_series.last_season_id = list(got_cached_rezka_data.seasons.keys())[-1]
                            db_track_series.last_episode_id = list(got_cached_rezka_data.episodes[db_track_series.last_season_id].keys())[-1]

                            await asyncio.sleep(config.track_series_checker_per_delay)

                            continue

                        subupdates: list[str] = []

                        raw_seasons_data = got_cached_rezka_data.seasons
                        raw_seasons_ids = list(raw_seasons_data.keys())
                        raw_last_season_episodes_data = got_cached_rezka_data.episodes[last_season_id]
                        raw_last_season_episodes_ids = list(raw_last_season_episodes_data.keys())

                        last_season_id_index = raw_seasons_ids.index(last_season_id)
                        last_episode_id_index = raw_last_season_episodes_ids.index(last_episode_id)
                        last_season_title = raw_seasons_data[last_season_id]

                        if len(raw_last_season_episodes_data) - 1 > last_episode_id_index:
                            if len(raw_last_season_episodes_data) - 1 - last_episode_id_index > 1:
                                episode_start_id = raw_last_season_episodes_ids[last_episode_id_index + 1]
                                episode_end_id = raw_last_season_episodes_ids[-1]

                                subupdates.append(
                                    TEXTS.track_series.updates.episodes.format(
                                        episode_start_digit = utils.extract_digits_from_string(raw_last_season_episodes_data[episode_start_id]),
                                        episode_end_digit = utils.extract_digits_from_string(raw_last_season_episodes_data[episode_end_id]),
                                        season_digit = utils.extract_digits_from_string(last_season_title)
                                    )
                                )

                            else:
                                episode_id = raw_last_season_episodes_ids[-1]

                                subupdates.append(
                                    TEXTS.track_series.updates.episode.format(
                                        episode_digit = utils.extract_digits_from_string(raw_last_season_episodes_data[episode_id]),
                                        season_digit = utils.extract_digits_from_string(last_season_title)
                                    )
                                )

                            db_track_series.last_episode_id = raw_last_season_episodes_ids[-1]

                        if len(raw_seasons_data) - 1 > last_season_id_index:
                            for season_id in raw_seasons_ids[last_season_id_index + 1:]:
                                season_title = raw_seasons_data[season_id]
                                episodes_data = got_cached_rezka_data.episodes.get(season_id, {})

                                if not episodes_data:
                                    continue

                                episodes_ids = list(episodes_data.keys())

                                if len(episodes_data) > 1:
                                    episode_start_id = episodes_ids[0]
                                    episode_end_id = episodes_ids[-1]

                                    subupdates.append(
                                        TEXTS.track_series.updates.season_episodes.format(
                                            episode_start_digit = utils.extract_digits_from_string(episodes_data[episode_start_id]),
                                            episode_end_digit = utils.extract_digits_from_string(episodes_data[episode_end_id]),
                                            season_digit = utils.extract_digits_from_string(season_title)
                                        )
                                    )

                                else:
                                    episode_id = episodes_ids[-1]

                                    subupdates.append(
                                        TEXTS.track_series.updates.season_episode.format(
                                            episode_digit = utils.extract_digits_from_string(episodes_data[episode_id]),
                                            season_digit = utils.extract_digits_from_string(season_title)
                                        )
                                    )

                                db_track_series.last_season_id = season_id
                                db_track_series.last_episode_id = episodes_ids[-1]

                        if subupdates:
                            notify_updates.append((
                                db_track_series.item_title,
                                subupdates,
                                db_track_series.user_tg_ids,
                                db_track_series.user_tg_message_ids
                            ))

                await db_session.commit()

                for item_title, notify_updates_, user_tg_ids, user_tg_message_ids in notify_updates:
                    text = TEXTS.track_series.updates.default.format(
                        title = item_title,
                        updates = "\n".join(notify_updates_)
                    )

                    for user_tg_id, user_tg_message_id in zip(user_tg_ids, user_tg_message_ids):
                        try:
                            await bot.send_message(
                                chat_id = user_tg_id,
                                text = text,
                                reply_to_message_id = user_tg_message_id,
                                allow_sending_without_reply = True
                            )

                        except TelegramAPIError:
                            pass

                        await asyncio.sleep(config.track_series_checker_per_message_delay)

                if len(db_track_series_list) >= 1:
                    last_track_series_id = db_track_series_list[-1].id

            await asyncio.sleep(config.track_series_checker_per_delay)
