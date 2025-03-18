from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram import types
from cachetools import TTLCache

import typing

from src.basic_data import TEXTS


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, ttl: float) -> None:
        self.cache = TTLCache[int, float | None](
            maxsize = 10_000,
            ttl = ttl
        )

    async def __call__(
        self,
        handler: typing.Callable[[types.TelegramObject, dict[str, typing.Any]], typing.Awaitable[typing.Any]],
        event: types.Message | types.CallbackQuery | types.TelegramObject,
        data: dict[str, typing.Any]
    ) -> bool:
        message: types.Message | typing.Any = event

        if hasattr(message, "message"):
            message = getattr(message, "message")

        if message.chat.id in self.cache:
            if isinstance(event, types.Message):
                await event.answer(
                    text = TEXTS.errors.flood.message
                )

            elif isinstance(event, types.CallbackQuery):
                await event.answer(
                    text = TEXTS.errors.flood.callback_query,
                    show_alert = True
                )

            return False

        self.cache[message.chat.id] = None

        return await handler(event, data)
