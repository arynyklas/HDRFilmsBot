from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram import types

import sqlalchemy as sa
import typing

from src import db


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: typing.Callable[[types.TelegramObject, dict[str, typing.Any]], typing.Awaitable[typing.Any]],
        event: types.TelegramObject,
        data: dict[str, typing.Any]
    ) -> typing.Any:
        if isinstance(event, types.CallbackQuery) and (not event.message or isinstance(event.message, types.InaccessibleMessage)):
            return

        event = typing.cast(types.Message | types.CallbackQuery, event)

        user_tg_id = event.from_user.id  # type: ignore

        db_session: db.DBSession = data["db_session"]

        db_user = (await db_session.execute(
            sa.select(db.User)
            .where(
                db.User.tg_id == user_tg_id
            )
        )).scalar()

        if db_user is None:
            if isinstance(event, types.Message) is False:
                return False

            db_user = db.User(
                tg_id = user_tg_id
            )

            db_session.add(db_user)

            await db_session.commit()

        data["db_user"] = db_user

        return await handler(event, data)
