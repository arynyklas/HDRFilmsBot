from aiogram import types

import sqlalchemy as sa

from src import db, utils, keyboards, constants
from src.cache import AsyncTimedRezkaCacheData, AsyncTimedRezkaCacheShortInfo
from src.basic_data import TEXTS, KB_TEXTS
from src.config import config
from .update_translators import process_update_translators_callback_query


async def item_callback_query_handler(
    callback_query: types.CallbackQuery,
    all_args: list[str],
    db_user: db.User,
    db_session: db.DBSession,
    rezka_cache_data: AsyncTimedRezkaCacheData,
    rezka_cache_short_info: AsyncTimedRezkaCacheShortInfo
):
    message: types.Message = callback_query.message  # type: ignore

    if all_args[1] != constants.VERSION_STR:
        await message.edit_text(
            text = TEXTS.data_updated.message,
            reply_markup = keyboards.start_markup
        )

        await callback_query.answer(
            text = TEXTS.data_updated.inline,
            show_alert = True
        )

        return

    args = all_args[2:]

    item_id = args[0]
    is_film = bool(int(args[1]))

    if len(args) == 2:
        await process_update_translators_callback_query(
            callback_query = callback_query,
            item_id = item_id,
            rezka_cache_short_info = rezka_cache_short_info
        )

        await callback_query.answer()

        return

    translator_data = args[2].split("|")

    translator_id = translator_data[0]

    if len(translator_data) == 2 and translator_data[1]:
        translator_additional_arguments = utils.parse_inline_translator_additional_arguments(translator_data[1])
    else:
        translator_additional_arguments = {}

    reply_to_message: types.Message = message.reply_to_message  # type: ignore

    title, url = utils.parse_item_message(reply_to_message)  # type: ignore

    if len(args) == 3 or (len(args) == 4 and args[3] == "update"):
        translator_title_temp: str | None = None

        try:
            translator_title_temp = utils.extract_translator_from_buttons_message(message)

        except Exception:
            pass

        if not translator_title_temp or translator_title_temp == KB_TEXTS.subscription.back:
            _, translators = await rezka_cache_short_info.get_or_set(url)

            for translator in translators:
                if translator.id == translator_id:
                    translator_title_temp = translator.title

                    break

        if not translator_title_temp:
            raise RuntimeError("Translator title not found")

        translator_title = translator_title_temp

        got_cached_rezka_data = await rezka_cache_data.get_or_set(
            item_id = item_id,
            item_title = title,
            translator_id = translator_id,
            translator_title = translator_title,
            translator_additional_arguments = translator_additional_arguments,
            is_film = is_film
        )

        if is_film:
            if not got_cached_rezka_data.urls:
                await message.edit_text(
                    text = TEXTS.not_avaliable.default_with_translator.format(
                        translator = translator_title
                    )
                )

                await callback_query.answer()

                return

            await message.edit_text(
                text = TEXTS.enjoy.default.format(
                    series_text = "",
                    translator = translator_title
                ),
                reply_markup = keyboards.direct_urls(
                    direct_urls = got_cached_rezka_data.urls,
                    is_film = is_film,
                    external_player_url = utils.get_external_player_url(
                        external_player_url = config.external_player_url,
                        item_id = item_id,
                        title = title,
                        translator_title = translator_title,
                        is_film = is_film,
                        direct_urls = got_cached_rezka_data
                    ),
                    item_id = item_id,
                    subtitles = got_cached_rezka_data.subtitles,
                    translator_id = translator_id,
                    translator_additional_arguments = translator_additional_arguments
                )
            )

            if len(args) == 4:
                await callback_query.answer(
                    text = TEXTS.updated
                )

            else:
                await callback_query.answer()

            return

        if not got_cached_rezka_data.seasons:
            await message.edit_text(
                text = TEXTS.not_avaliable.default_with_translator.format(
                    translator = translator_title
                )
            )

            await callback_query.answer()

            return

        await message.edit_text(
            text = TEXTS.select.season.format(
                translator = translator_title
            ),
            reply_markup = keyboards.seasons(
                item_id = item_id,
                translator_id = translator_id,
                translator_additional_arguments = translator_additional_arguments,
                seasons = got_cached_rezka_data.seasons
            )
        )

    elif len(args) >= 4 and args[3] == "download":
        arg_index: int = all_args.index("download")

        if await db.utils.user_has_active_subscription(db_user, db_session) is False:
            await message.edit_text(
                text = TEXTS.subscription.default.format(
                    days = config.subscription.days,
                    price = config.subscription.price
                ),
                reply_markup = keyboards.subscription(
                    data = "_".join(all_args[:arg_index] + all_args[arg_index + 1:])
                )
            )

            await callback_query.answer()

            return

        season_id_temp: str | None = None
        episode_id_temp: str | None = None

        if len(args) > 4:
            season_id_temp = args[4]
            episode_id_temp = args[5]

        db_downloaded_item = (await db_session.execute(
            sa.select(db.DownloadedItem)
            .where(
                db.DownloadedItem.item_id == item_id,
                db.DownloadedItem.translator_id == translator_id,
                *(
                    (
                        db.DownloadedItem.season_id == season_id_temp,
                        db.DownloadedItem.episode_id == episode_id_temp
                    )
                    if season_id_temp is not None
                    else
                    ()
                )
            )
        )).scalar()

        if db_downloaded_item:
            await reply_to_message.reply_video(
                video = db_downloaded_item.video_file_id,  # type: ignore  # TODO: fix type hint
                caption = TEXTS.select.download_quality_statuses.caption.default.format(
                    item_title = db_downloaded_item.item_title,
                    series_text = (
                        TEXTS.select.download_quality_statuses.caption.series_test.format(
                            season_id = db_downloaded_item.season_id,
                            episode_id = db_downloaded_item.episode_id
                        )
                        if db_downloaded_item.season_id  # type: ignore  # TODO: fix type hint
                        else
                        ""
                    ),
                    translator = db_downloaded_item.translator_title,
                    quality = db_downloaded_item.quality
                ),
                protect_content = True
            )

            await callback_query.answer()

            return

        translator_title = utils.extract_translator_from_buttons_message(message)

        got_cached_rezka_data = await rezka_cache_data.get_or_set(
            item_id = item_id,
            item_title = title,
            translator_id = translator_id,
            translator_title = translator_title,
            translator_additional_arguments = translator_additional_arguments,
            is_film = is_film,
            season_id = season_id_temp,
            episode_id = episode_id_temp
        )

        bot_message = await reply_to_message.reply(
            text = TEXTS.select.download_quality_statuses.queue
        )

        db_download_item_queue = (await db_session.execute(
            sa.select(db.DownloadItemQueue)
            .where(
                db.DownloadItemQueue.item_id == item_id,
                db.DownloadItemQueue.translator_id == translator_id
            )
        )).scalar()

        if db_download_item_queue and callback_query.from_user.id not in db_download_item_queue.user_tg_ids:
            db_download_item_queue.user_tg_ids.append(callback_query.from_user.id)
            db_download_item_queue.user_tg_message_ids.append(bot_message.message_id)
            db_download_item_queue.user_tg_reply_message_ids.append(reply_to_message.message_id)

            await db_session.commit()

        elif not db_download_item_queue:
            db_download_item_queue = db.DownloadItemQueue(
                item_id = item_id,
                item_title = title,
                translator_id = translator_id,
                translator_title = translator_title,
                translator_additional_arguments = translator_additional_arguments,
                is_film = is_film,
                season_id = season_id_temp,
                episode_id = episode_id_temp,
                user_tg_ids = [callback_query.from_user.id],
                user_tg_message_ids = [bot_message.message_id],
                user_tg_reply_message_ids = [reply_to_message.message_id]
            )

            db_session.add(db_download_item_queue)

            await db_session.commit()

    elif len(args) >= 4 and args[3] == "track":
        db_track_series = (await db_session.execute(
            sa.select(db.TrackSeries)
            .where(
                db.TrackSeries.item_id == item_id,
                db.TrackSeries.translator_id == translator_id
            )
        )).scalar()

        if db_track_series and callback_query.from_user.id not in db_track_series.user_tg_ids:
            db_track_series.user_tg_ids.append(callback_query.from_user.id)
            db_track_series.user_tg_message_ids.append(reply_to_message.message_id)

            await db_session.commit()

        elif not db_track_series:
            season_id, episode_id = utils.extract_series_data_from_message(message)

            translator_title = utils.extract_translator_from_buttons_message(message)

            db_track_series = db.TrackSeries(
                item_id = item_id,
                item_title = title,
                translator_id = translator_id,
                translator_title = translator_title,
                translator_additional_arguments = translator_additional_arguments,
                user_tg_ids = [callback_query.from_user.id],
                user_tg_message_ids = [reply_to_message.message_id],
                last_season_id = season_id,
                last_episode_id = episode_id
            )

            db_session.add(db_track_series)

            await db_session.commit()

        reply_markup = message.reply_markup
        inline_keyboard = reply_markup.inline_keyboard  # type: ignore

        for row_index, row in enumerate(inline_keyboard):
            break_ = False

            for button_index, button in enumerate(row):
                if button.callback_data == callback_query.data:
                    if len(row) == 1:
                        del inline_keyboard[row_index]
                    else:
                        del inline_keyboard[row_index][button_index]

                    break_ = True

                    break

            if break_:
                break

        await message.edit_reply_markup(
            reply_markup = reply_markup
        )

        await reply_to_message.reply(
            text = TEXTS.track_series.default
        )

    elif len(args) == 4:
        season_id = args[3]

        translator_title = utils.extract_translator_from_buttons_message(message)

        got_cached_rezka_data = await rezka_cache_data.get_or_set(
            item_id = item_id,
            item_title = title,
            translator_id = translator_id,
            translator_title = translator_title,
            translator_additional_arguments = translator_additional_arguments,
            is_film = is_film
        )

        await message.edit_text(
            text = TEXTS.select.episode.format(
                season_id = season_id,
                translator = translator_title
            ),
            reply_markup = keyboards.episodes(
                item_id = item_id,
                translator_id = translator_id,
                translator_additional_arguments = translator_additional_arguments,
                season_id = season_id,
                episodes = got_cached_rezka_data.episodes[season_id]  # type: ignore
            )
        )

    else:
        season_id = args[3]
        episode_id = args[4]

        translator_title: str | None = None

        try:
            translator_title = utils.extract_translator_from_buttons_message(message)

        except Exception:
            pass

        if not translator_title or translator_title == KB_TEXTS.subscription.back:
            _, translators = await rezka_cache_short_info.get_or_set(url)

            for translator in translators:
                if translator.id == translator_id:
                    translator_title = translator.title

                    break

        if not translator_title:
            raise RuntimeError("Translator title not found")

        got_cached_rezka_data = await rezka_cache_data.get_or_set(
            item_id = item_id,
            item_title = title,
            translator_id = translator_id,
            translator_title = translator_title,
            translator_additional_arguments = translator_additional_arguments,
            is_film = is_film,
            season_id = season_id,
            episode_id = episode_id
        )

        got_clean_cached_rezka_data = await rezka_cache_data.get_or_set(
            item_id = item_id,
            item_title = title,
            translator_id = translator_id,
            translator_title = translator_title,
            translator_additional_arguments = translator_additional_arguments,
            is_film = is_film
        )

        season_index: int | None = None
        season_title: str | None = None
        episode_index: int | None = None
        episode_title: str | None = None

        seasons: dict[str, str] = got_clean_cached_rezka_data.seasons  # type: ignore
        all_episodes: dict[str, dict[str, str]] = got_clean_cached_rezka_data.episodes  # type: ignore

        for index, (season_id_, season_title_) in enumerate(seasons.items(), 0):
            if season_id_ == season_id:
                season_index = index
                season_title = season_title_

                break

        for index, (episode_id_, episode_title_) in enumerate(all_episodes[season_id].items(), 0):
            if episode_id_ == episode_id:
                episode_index = index
                episode_title = episode_title_

                break

        if season_index is None or episode_index is None or not got_cached_rezka_data.urls:
            await message.edit_text(
                text = TEXTS.not_avaliable.default_with_translator.format(
                    translator = translator_title
                )
            )

            await callback_query.answer()

            return

        await message.edit_text(
            text = TEXTS.enjoy.default.format(
                series_text = TEXTS.enjoy.series.format(
                    season_id = season_id,
                    episode_id = episode_id,
                ),
                translator = translator_title
            ),
            reply_markup = keyboards.direct_urls(
                direct_urls = got_cached_rezka_data.urls,
                subtitles = got_cached_rezka_data.subtitles,
                is_film = is_film,
                external_player_url = utils.get_external_player_url(
                    external_player_url = config.external_player_url,
                    item_id = item_id,
                    title = title,
                    translator_title = translator_title,
                    is_film = is_film,
                    direct_urls = got_cached_rezka_data,
                    season_id = season_id,
                    season_title = season_title,
                    episode_id = episode_id,
                    episode_title = episode_title
                ),
                item_id = item_id,
                translator_id = translator_id,
                translator_additional_arguments = translator_additional_arguments,
                season_id = season_id,
                episode_id = episode_id,
                prev_season_id = (
                    list(seasons.keys())[season_index - 1]
                    if season_index > 0
                    else
                    None
                ),
                prev_episode_id = (
                    list(all_episodes[season_id].keys())[episode_index - 1]
                    if episode_index > 0
                    else
                    None
                ),
                next_episode = (
                    list(all_episodes[season_id].keys())[episode_index + 1]
                    if episode_index < len(all_episodes[season_id]) - 1
                    else
                    None
                ),
                next_season = (
                    list(seasons.keys())[season_index + 1]
                    if season_index < len(seasons) - 1
                    else
                    None
                ),
                add_track_series = (
                    (await db_session.execute(
                        sa.select(sa.exists()
                        .where(
                            db.TrackSeries.item_id == item_id,
                            db.TrackSeries.translator_id == translator_id,
                            db.TrackSeries.user_tg_ids.contains([callback_query.from_user.id])
                        ))
                    )).scalar_one()
                ) == 0
            )
        )

        if len(args) == 6 and args[5] == "update":
            await callback_query.answer(
                text = TEXTS.updated
            )

            return
