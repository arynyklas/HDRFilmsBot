from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

import typing

from src import db


class DBSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool: db.DBSessionMaker) -> None:
        super().__init__()

        self.session_pool = session_pool

    async def __call__(
        self,
        handler: typing.Callable[[TelegramObject, dict[str, typing.Any]], typing.Awaitable[typing.Any]],
        event: TelegramObject,
        data: dict[str, typing.Any],
    ) -> typing.Any:
        async with self.session_pool() as db_session:
            data["db_session"] = db_session

            return await handler(event, data)
