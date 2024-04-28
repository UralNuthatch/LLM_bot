from aiogram import Router
from aiogram.types import Message
from fluentogram import TranslatorRunner


router = Router()

# Этот хэндлер используется как отбойник
@router.message()
async def send_unsupported_format(message: Message, i18n: TranslatorRunner):
    await message.answer(i18n.wrong.format())