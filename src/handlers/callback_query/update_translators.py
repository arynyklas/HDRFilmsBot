from aiogram import types

from src import utils, keyboards
from src.cache import AsyncTimedRezkaCacheShortInfo
from src.basic_data import TEXTS


async def process_update_translators_callback_query(
    callback_query: types.CallbackQuery,
    item_id: str,
    rezka_cache_short_info: AsyncTimedRezkaCacheShortInfo
) -> None:
    message: types.Message = callback_query.message  # type: ignore

    _, url = utils.parse_item_message(message.reply_to_message)  # type: ignore

    short_info, translators = await rezka_cache_short_info.get_or_set(url)

    if short_info.is_film is None or not translators:
        await message.edit_text(
            text = TEXTS.not_avaliable.default
        )

        return

    await message.edit_text(
        text = TEXTS.select.translator,
        reply_markup = keyboards.translators(
            item_id = item_id,
            is_film = short_info.is_film,
            translators = translators
        )
    )
