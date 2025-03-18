from logging import Logger
from logging.handlers import RotatingFileHandler
from telegram_bot_logger import TelegramMessageHandler, formatters as logger_formatters
from pathlib import Path
from urllib.parse import urlparse
from time import time
from datetime import datetime, timezone
from aiogram import types
from rezka_api_sdk import models as rezka_models

import logging
import sys
import typing

from src import models, constants, encrypt_utils


DEFAULT_LOG_FORMAT = "%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"

T = typing.TypeVar("T")
K = typing.TypeVar("K")
V = typing.TypeVar("V")


def get_logger(name: str, bot_token: str, chat_ids: int | str | list[int | str], filepath: Path, logger_chat_level: str, logger_file_level: str) -> Logger:
    logger = logging.getLogger(name)

    telegram_handler = TelegramMessageHandler(
        bot_token = bot_token,
        chat_ids = chat_ids,
        format_type = logger_formatters.FormatType.DOCUMENT,
        document_name_strategy = logger_formatters.DocumentNameStrategy.ARGUMENT,
        formatter = logger_formatters.TelegramHTMLTextFormatter(),
        level = logger_chat_level
    )

    logger.addHandler(telegram_handler)

    file_handler = RotatingFileHandler(
        filename = filepath.resolve().as_posix(),
        mode = "a",
        maxBytes = 10_485_760,  # 10 MB
        backupCount = 1_000,
        encoding = "utf-8"
    )

    default_formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
    file_handler.setFormatter(default_formatter)
    file_handler.setLevel(logger_file_level)

    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(default_formatter)
    console_handler.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)

    logger.setLevel(logging.DEBUG)

    return logger


def chunker(collection: list[T], n: int) -> list[list[T]]:
    return [
        collection[i:i + n]
        for i in range(0, len(collection), n)
    ]


def dict_chunker(collection: dict[K, V], n: int) -> list[dict[K, V]]:
    keys = list(collection.keys())

    return [
        {
            key: collection[key]
            for key in keys[i:i + n]
        }
        for i in range(0, len(keys), n)
    ]


def sort_direct_urls(direct_urls: dict[str, str]) -> dict[str, str]:
    return dict(sorted(
        direct_urls.items(),
        key = lambda item: int(extract_digits_from_string(item[0]))
    ))


def rezka_is_film_by_url(url: str) -> bool:
    return urlparse(url).path.split("/")[1] == "films"


def rezka_extract_id_from_url(url: str) -> str:
    return urlparse(url).path.split("/")[3].split("-", 1)[0]


def extract_digits_from_string(string: str) -> str:
    return "".join(filter(str.isdigit, string))


def get_timestamp_float() -> float:
    return time()

def get_timestamp_int() -> int:
    return int(get_timestamp_float())


def get_datetime_utcnow() -> datetime:
    return datetime.now(timezone.utc)

def timestamp_to_datetime(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp, timezone.utc)


def parse_inline_translator_additional_arguments(translator_additional_arguments_str: str) -> dict[str, str]:
    translator_additional_arguments: dict[str, str] = dict()

    for translator_is_argument_line in translator_additional_arguments_str.split("&"):
        translator_is_argument_line: str

        translator_is_argument_key: str
        translator_is_argument_value: str

        translator_is_argument_key, translator_is_argument_value = translator_is_argument_line.split("=")

        translator_additional_arguments[translator_is_argument_key] = translator_is_argument_value

    return translator_additional_arguments


def parse_item_message(message: types.Message) -> tuple[str, str]:
    # NOTE: src/basic_data.py => TEXTS.inline_search.message_content
    return message.text.replace("⁣", "", 1).split("\n", 1)  # type: ignore


def extract_translator_from_buttons_message(message: types.Message) -> str:
    result = constants.TRANSLATOR_TEXT_PATTERN.search(message.html_text)

    if not result:
        raise ValueError("Translator not found")

    return result.group(1)

def extract_series_data_from_message(message: types.Message) -> tuple[str, str]:
    text = typing.cast(str, message.text)

    result = constants.SERIES_DATA_PATTERN.search(text)

    if not result:
        raise ValueError("Series data not found")

    return (result.group(1), result.group(2))


def get_external_player_url(
    external_player_url: str | None,
    item_id: str,
    title: str,
    translator_title: str,
    is_film: bool,
    direct_urls: rezka_models.DirectURLsModel | models.CachedRezkaData,
    season_id: str | None = None,
    season_title: str | None = None,
    episode_id: str | None = None,
    episode_title: str | None = None
) -> str | None:
    if not external_player_url:
        return

    external_data = {
        "id": item_id,
        "title": title,
        "translator_title": translator_title,
        "is_film": is_film,
        "urls": direct_urls.urls
    }

    if direct_urls.subtitles:
        external_data["subtitles"] = direct_urls.subtitles
        external_data["subtitle_languages"] = direct_urls.subtitle_languages

    if not is_film:
        external_data.update({
            "season_id": season_id,
            "season_title": season_title,
            "episode_id": episode_id,
            "episode_title": episode_title
        })

    return external_player_url + "#" + encrypt_utils.encrypt(external_data)
