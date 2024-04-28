from aiogram import Bot


async def send_no_key(bot: Bot):
    await bot.send_message(chat_id=348123497, text='закончились ключи для stability')