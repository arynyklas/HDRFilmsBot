from aiogram import Bot, Dispatcher, types, enums as aiogram_enums, exceptions, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.client.default import DefaultBotProperties
from sqlalchemy.ext.asyncio import create_async_engine as create_db_engine
from rezka_api_sdk import RezkaAPI
from aiohttp.client_exceptions import ServerDisconnectedError

import asyncio
import logging
import typing

from src import db, middlewares, utils, constants, background_tasks
from src.cache import AsyncTimedRezkaCacheData, AsyncTimedRezkaCacheShortInfo
from src.handlers import ROUTERS
from src.config import config


REZKA_API_TIMEOUT = 20.

IGNORE_EXCEPTIONS_STR_LIST = (
    "message was deleted",
    "canceled by new editmessagemedia request",
    "query is too old",
)

IGNORE_EXCEPTIONS_LIST = (
    asyncio.CancelledError,
    ServerDisconnectedError,
)


dispatcher = Dispatcher()

bot = Bot(
    token = config.bot_token,
    session = AiohttpSession(
        api = TelegramAPIServer.from_base(
            base = config.custom_bot_api_server,
            is_local = True
        ),
        timeout = 10.
    ),
    default = DefaultBotProperties(
        parse_mode = aiogram_enums.ParseMode.HTML
    )
)


rezka_api = RezkaAPI(
    api_key = config.rezka_api_key,
    timeout = REZKA_API_TIMEOUT
)

if config.rezka_api_url:
    rezka_api.API_URL = config.rezka_api_url  # type: ignore


logging.getLogger('sqlalchemy.engine.Engine').disabled = True


logger = utils.get_logger(
    name = config.logger_name,
    bot_token = config.bot_token,
    chat_ids = config.logs_chat_id,
    filepath = constants.LOGS_DIRPATH / config.log_filename,
    logger_chat_level = config.logger_chat_level,
    logger_file_level = config.logger_file_level
)

rezka_cache_data = AsyncTimedRezkaCacheData(
    rezka_api = rezka_api,
    expiration_time = config.cache_rezka_data_time
)

rezka_cache_short_info = AsyncTimedRezkaCacheShortInfo(
    rezka_api = rezka_api,
    expiration_time = config.cache_rezka_data_time
)

db_engine = create_db_engine(
    url = config.db_url,
    echo = True
)

db_sessionmaker = db.DBSessionMaker(
    bind = db_engine,
    expire_on_commit = False,
    autoflush = False
)


for middleware in [
    middlewares.ThrottlingMiddleware(
        ttl = 1 / config.users_messages_per_second
    ),
    middlewares.DBSessionMiddleware(
        session_pool = db_sessionmaker
    ),
    middlewares.UserMiddleware()
]:
    for event_observer in (
        dispatcher.message,
        dispatcher.callback_query,
    ):
        event_observer.middleware.register(middleware)


dispatcher.callback_query.filter(F.message.chat.type == aiogram_enums.ChatType.PRIVATE)
dispatcher.message.filter(F.chat.type == aiogram_enums.ChatType.PRIVATE)


@dispatcher.error()
async def error_handler(event: types.ErrorEvent) -> None:
    if event.exception.__class__ in IGNORE_EXCEPTIONS_LIST:
        return

    if isinstance(event.exception, exceptions.TelegramBadRequest) and event.exception.message:
        exception_message: str = event.exception.message.lower()

        for string in IGNORE_EXCEPTIONS_STR_LIST:
            if string in exception_message:
                return

    logger.exception(
        msg = event.update.model_dump_json(
            exclude_unset = True
        ),
        exc_info = event.exception,
        extra = dict(
            document_name = str(event.update.update_id)
        )
    )


@dispatcher.startup()
async def on_startup() -> None:
    bot_username = (await bot.me()).username

    logger.info(f"Starting @{bot_username}...")

    asyncio.create_task(utils.logger_wrapper(logger, background_tasks.db_track_series_checker(bot, db_sessionmaker, rezka_cache_data, logger)))
    asyncio.create_task(utils.logger_wrapper(logger, background_tasks.download_items_queue_worker(bot, db_sessionmaker, rezka_cache_data)))
    asyncio.create_task(utils.logger_wrapper(logger, background_tasks.cleanup_expired_cache_worker(rezka_cache_data, rezka_cache_short_info)))


dispatcher_workflow: dict[str, typing.Any] = dict(
    logger = logger,
    rezka_api = rezka_api,
    rezka_cache_data = rezka_cache_data,
    rezka_cache_short_info = rezka_cache_short_info
)


dispatcher.include_routers(*ROUTERS)
