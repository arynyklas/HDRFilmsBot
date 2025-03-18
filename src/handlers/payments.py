from aiogram import Router, types, F

from src import db, utils, enums
from src.basic_data import TEXTS
from src.config import config


payments_router = Router()


@payments_router.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: types.PreCheckoutQuery) -> None:
    await pre_checkout_query.answer(
        ok = (
            pre_checkout_query.currency == config.subscription.currency and 
            pre_checkout_query.total_amount == config.subscription.price and
            pre_checkout_query.invoice_payload == str(enums.PaymentPurposeEnum.SUBSCRIPTION.value)
        )
    )


@payments_router.message(F.successful_payment)
async def successful_payment_handler(
    message: types.Message,
    db_user: db.User,
    db_session: db.DBSession,
    logger: utils.Logger
) -> None:
    successful_payment: types.SuccessfulPayment = message.successful_payment  # type: ignore

    db_payment = db.Payment(
        user_id = db_user.id,
        amount = successful_payment.total_amount,
        currency = enums.CurrencyEnum.XTR,
        purpose = enums.PaymentPurposeEnum(int(successful_payment.invoice_payload)),
        tg_charge_id = successful_payment.telegram_payment_charge_id
    )

    db_session.add(db_payment)

    await db_session.flush()

    db_session.add(db.Subscription(
        user_id = db_user.id,
        payment_id = db_payment.id,
        expiration_datetime = utils.timestamp_to_datetime(utils.get_timestamp_int() + (config.subscription.days * 24 * 60 * 60))
    ))

    await db_session.commit()

    await message.answer(
        text = TEXTS.subscription.paid.format(
            days = config.subscription.days
        )
    )

    logger.info("Payment successful: user_id={}, user_tg_id={}, payment_id={}".format(
        db_user.id,
        db_user.tg_id,
        db_payment.id
    ))
