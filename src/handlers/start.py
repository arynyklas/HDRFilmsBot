from aiogram import Router, types, filters

from src import keyboards
from src.basic_data import TEXTS


start_router = Router()


@start_router.message(filters.Command("start"))
async def start_command_handler(message: types.Message) -> None:
    await message.answer(
        text = TEXTS.start,
        reply_markup = keyboards.start_markup
    )
