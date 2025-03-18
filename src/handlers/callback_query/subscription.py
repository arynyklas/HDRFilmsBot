from aiogram import types

from src import db, enums
from src.basic_data import TEXTS
from src.config import config


async def subscription_callback_query_handler(
    callback_query: types.CallbackQuery,
    db_user: db.User,
    db_session: db.DBSession
):
    message: types.Message = callback_query.message  # type: ignore

    if await db.utils.user_has_active_subscription(db_user, db_session) is False:
        await message.answer_invoice(
            title = TEXTS.subscription.invoice.title,
            description = TEXTS.subscription.invoice.description,
            payload = str(enums.PaymentPurposeEnum.SUBSCRIPTION.value),
            currency = config.subscription.currency,
            prices = [
                types.LabeledPrice(
                    label = TEXTS.subscription.invoice.price_label.format(
                        days = config.subscription.days
                    ),
                    amount = config.subscription.price
                )
            ],
            protect_content = True
        )

    reply_markup: types.InlineKeyboardMarkup = message.reply_markup  # type: ignore

    del reply_markup.inline_keyboard[0][0]

    await message.edit_reply_markup(
        reply_markup = reply_markup
    )

    await callback_query.answer()
