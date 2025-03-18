from aiogram import Router, types

from src import db
from src.cache import AsyncTimedRezkaCacheData, AsyncTimedRezkaCacheShortInfo
from .item import item_callback_query_handler
from .subscription import subscription_callback_query_handler


callback_query_router = Router()


@callback_query_router.callback_query()
async def callback_query_handler(
    callback_query: types.CallbackQuery,
    db_user: db.User,
    db_session: db.DBSession,
    rezka_cache_data: AsyncTimedRezkaCacheData,
    rezka_cache_short_info: AsyncTimedRezkaCacheShortInfo
) -> None:
    if not callback_query.data:
        await callback_query.answer()

        return

    all_args = callback_query.data.split("_")

    if all_args[0] == "null":
        pass

    elif all_args[0] == "item":
        await item_callback_query_handler(
            callback_query = callback_query,
            all_args = all_args,
            db_user = db_user,
            db_session = db_session,
            rezka_cache_data = rezka_cache_data,
            rezka_cache_short_info = rezka_cache_short_info
        )

    elif all_args[0] == "subscription":
        await subscription_callback_query_handler(
            callback_query = callback_query,
            db_user = db_user,
            db_session = db_session
        )

    await callback_query.answer()
