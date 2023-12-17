from aiogram import Router
from aiogram.types import Message
from lexicon.lexicon import LEXICON


router = Router()

# Этот хэндлер используется как отбойник
@router.message()
async def send_unsupported_format(message: Message):
    await message.answer(LEXICON["wrong_message"])