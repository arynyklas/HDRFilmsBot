from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from urllib.parse import urlencode
from rezka_api_sdk import models as rezka_models

from src import utils, constants
from src.basic_data import KB_TEXTS


DIRECT_URLS_CHUNK_SIZE = 2
SUBTITLES_CHUNK_SIZE = DIRECT_URLS_CHUNK_SIZE
NULL_TEXT = " "
NULL_CALLBACK = "null"


start_markup = InlineKeyboardMarkup(
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text = KB_TEXTS.inline,
                switch_inline_query_current_chat = ""
            )
        ]
    ]
)


def translators(item_id: str, is_film: bool, translators: list[rezka_models.TranslatorInfoModel]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard = [
            [
                InlineKeyboardButton(
                    text = translator.title,
                    callback_data = "item_{version}_{item_id}_{is_film}_{translator_id}|{translator_additional_arguments}".format(
                        version = constants.VERSION_STR,
                        item_id = item_id,
                        is_film = int(is_film),
                        translator_id = translator.id,
                        translator_additional_arguments = urlencode(translator.additional_arguments)
                    )
                )
            ]
            for translator in translators
        ]
    )


def direct_urls(
    direct_urls: dict[str, str],
    is_film: bool,
    external_player_url: str | None = None,
    item_id: str | None = None,
    translator_id: str | None = None,
    translator_additional_arguments: dict[str, str] = {},
    season_id: str | None = None,
    episode_id: str | None = None,
    prev_season_id: str | None = None,
    prev_episode_id: str | None = None,
    next_episode: str | None = None,
    next_season: str | None = None,
    subtitles: dict[str, str] | None = None,
    add_track_series: bool | None = None
) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(
        inline_keyboard = [
            *[
                [
                    InlineKeyboardButton(
                        text = quality,
                        url = direct_url
                    )
                    for quality, direct_url in direct_urls_.items()
                ]
                for direct_urls_ in utils.dict_chunker(
                    dict(reversed(
                        utils.sort_direct_urls(direct_urls).items()
                    )),
                    DIRECT_URLS_CHUNK_SIZE
                )
            ]
        ]
    )

    if external_player_url:
        markup.inline_keyboard.append([
            InlineKeyboardButton(
                text = KB_TEXTS.external_player_url,
                url = external_player_url
            )
        ])

    is_film_int = int(is_film)
    encoded_translator_additional_arguments = urlencode(translator_additional_arguments)

    markup.inline_keyboard.append([
        InlineKeyboardButton(
            text = KB_TEXTS.update,
            callback_data = "item_{version}_{item_id}_{is_film}_{translator_id}|{translator_additional_arguments}{series_data}_update".format(
                version = constants.VERSION_STR,
                item_id = item_id,
                is_film = is_film_int,
                translator_id = translator_id,
                translator_additional_arguments = encoded_translator_additional_arguments,
                series_data = (
                    ""
                    if is_film
                    else
                    "_{season_id}_{episode_id}".format(
                        season_id = season_id,
                        episode_id = episode_id
                    )
                )
            )
        )
    ])

    if subtitles:
        markup.inline_keyboard.append([
            InlineKeyboardButton(
                text = KB_TEXTS.subtitle,
                callback_data = NULL_CALLBACK
            )
        ])

        for subtitles_ in utils.dict_chunker(
            subtitles,
            SUBTITLES_CHUNK_SIZE
        ):
            markup.inline_keyboard.append([
                *[
                    InlineKeyboardButton(
                        text = subtitle_title,
                        url = subtitle_url
                    )
                    for subtitle_title, subtitle_url in subtitles_.items()
                ]
            ])

    markup.inline_keyboard.append([
        InlineKeyboardButton(
            text = KB_TEXTS.send_as_video,
            callback_data = "item_{version}_{item_id}_{is_film}_{translator_id}|{translator_additional_arguments}_download{series_data}".format(
                version = constants.VERSION_STR,
                item_id = item_id,
                is_film = is_film_int,
                translator_id = translator_id,
                translator_additional_arguments = encoded_translator_additional_arguments,
                series_data = (
                    ""
                    if is_film
                    else
                    "_{season_id}_{episode_id}".format(
                        season_id = season_id,
                        episode_id = episode_id
                    )
                )
            )
        )
    ])

    if is_film:
        markup.inline_keyboard.append([
            InlineKeyboardButton(
                text = KB_TEXTS.return_to_translators,
                callback_data = "item_{version}_{item_id}_{is_film}".format(
                    version = constants.VERSION_STR,
                    item_id = item_id,
                    is_film = int(is_film)
                )
            )
        ])

        return markup

    markup.inline_keyboard.append([
        InlineKeyboardButton(
            text = (
                "⏮"
                if prev_season_id
                else
                NULL_TEXT
            ),
            callback_data = (
                "item_{version}_{item_id}_{is_film}_{translator_id}|{translator_additional_arguments}_{season_id}".format(
                    version = constants.VERSION_STR,
                    item_id = item_id,
                    is_film = is_film_int,
                    translator_id = translator_id,
                    translator_additional_arguments = encoded_translator_additional_arguments,
                    season_id = prev_season_id
                )
                if prev_season_id
                else
                NULL_CALLBACK
            )
        )
    ])

    markup.inline_keyboard[-1].append(
        InlineKeyboardButton(
            text = (
                "⏪"
                if prev_episode_id
                else
                NULL_TEXT
            ),
            callback_data = (
                "item_{version}_{item_id}_{is_film}_{translator_id}|{translator_additional_arguments}_{season_id}_{episode_id}".format(
                    version = constants.VERSION_STR,
                    item_id = item_id,
                    is_film = is_film_int,
                    translator_id = translator_id,
                    translator_additional_arguments = encoded_translator_additional_arguments,
                    season_id = season_id,
                    episode_id = prev_episode_id
                )
                if prev_episode_id
                else
                NULL_CALLBACK
            )
        )
    )

    markup.inline_keyboard[-1].append(
        InlineKeyboardButton(
            text = (
                "⏩"
                if next_episode
                else
                NULL_TEXT
            ),
            callback_data = (
                "item_{version}_{item_id}_{is_film}_{translator_id}|{translator_additional_arguments}_{season_id}_{episode_id}".format(
                    version = constants.VERSION_STR,
                    item_id = item_id,
                    is_film = is_film_int,
                    translator_id = translator_id,
                    translator_additional_arguments = encoded_translator_additional_arguments,
                    season_id = season_id,
                    episode_id = next_episode
                )
                if next_episode
                else
                NULL_CALLBACK
            )
        )
    )

    markup.inline_keyboard[-1].append(
        InlineKeyboardButton(
            text = (
                "⏭"
                if next_season
                else
                NULL_TEXT
            ),
            callback_data = (
                "item_{version}_{item_id}_{is_film}_{translator_id}|{translator_additional_arguments}_{season_id}".format(
                    version = constants.VERSION_STR,
                    item_id = item_id,
                    is_film = is_film_int,
                    translator_id = translator_id,
                    translator_additional_arguments = encoded_translator_additional_arguments,
                    season_id = next_season
                )
                if next_season
                else
                NULL_CALLBACK
            )
        )
    )

    if add_track_series:
        markup.inline_keyboard.append([
            InlineKeyboardButton(
                text = KB_TEXTS.track_series,
                callback_data = "item_{version}_{item_id}_{is_film}_{translator_id}|{translator_additional_arguments}_track".format(
                    version = constants.VERSION_STR,
                    item_id = item_id,
                    is_film = is_film_int,
                    translator_id = translator_id,
                    translator_additional_arguments = encoded_translator_additional_arguments
                )
            )
        ])

    markup.inline_keyboard.append([
        InlineKeyboardButton(
            text = KB_TEXTS.all_seasons,
            callback_data = (
                "item_{version}_{item_id}_{is_film}_{translator_id}|{translator_additional_arguments}".format(
                    version = constants.VERSION_STR,
                    item_id = item_id,
                    is_film = is_film_int,
                    translator_id = translator_id,
                    translator_additional_arguments = encoded_translator_additional_arguments
                )
            )
        )
    ])

    return markup


def seasons(
    item_id: str,
    translator_id: str,
    translator_additional_arguments: dict[str, str],
    seasons: dict[str, str]
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard = [
            *[
                [
                    InlineKeyboardButton(
                        text = season_title,
                        callback_data = "item_{version}_{item_id}_{is_film}_{translator_id}|{translator_additional_arguments}_{season_id}".format(
                            version = constants.VERSION_STR,
                            item_id = item_id,
                            is_film = int(False),
                            translator_id = translator_id,
                            translator_additional_arguments = urlencode(translator_additional_arguments),
                            season_id = season_id
                        )
                    )
                ]
                for season_id, season_title in seasons.items()
            ],
            [
                InlineKeyboardButton(
                    text = KB_TEXTS.return_to_translators,
                    callback_data = "item_{version}_{item_id}_{is_film}".format(
                        version = constants.VERSION_STR,
                        item_id = item_id,
                        is_film = int(False)
                    )
                )
            ]
        ]
    )


def episodes(
    item_id: str,
    translator_id: str,
    translator_additional_arguments: dict[str, str],
    season_id: str,
    episodes: dict[str, str]
) -> InlineKeyboardMarkup:
    encoded_translator_additional_arguments = urlencode(translator_additional_arguments)

    return InlineKeyboardMarkup(
        inline_keyboard = [
            *[
                [
                    InlineKeyboardButton(
                        text = episode_title,
                        callback_data = "item_{version}_{item_id}_{is_film}_{translator_id}|{translator_additional_arguments}_{season_id}_{episode_id}".format(
                            version = constants.VERSION_STR,
                            item_id = item_id,
                            is_film = int(False),
                            translator_id = translator_id,
                            translator_additional_arguments = encoded_translator_additional_arguments,
                            season_id = season_id,
                            episode_id = episode_id
                        )
                    )
                ]
                for episode_id, episode_title in episodes.items()
            ],
            [
                InlineKeyboardButton(
                    text = KB_TEXTS.return_to_seasons,
                    callback_data = "item_{version}_{item_id}_{is_film}_{translator_id}|{translator_additional_arguments}".format(
                        version = constants.VERSION_STR,
                        item_id = item_id,
                        is_film = int(False),
                        translator_id = translator_id,
                        translator_additional_arguments = encoded_translator_additional_arguments
                    )
                )
            ]
        ]
    )


def subscription(data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard = [
            [
                InlineKeyboardButton(
                    text = KB_TEXTS.subscription.generate_invoice,
                    callback_data = "subscription"
                )
            ],
            [
                InlineKeyboardButton(
                    text = KB_TEXTS.subscription.back,
                    callback_data = data
                )
            ]
        ]
    )
