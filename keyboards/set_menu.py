from aiogram import Bot
from aiogram.types import BotCommand
from fluentogram import TranslatorRunner


# Функция для настройки кнопки Menu бота
async def set_main_menu(bot: Bot, i18n: TranslatorRunner):
    commands = {"/models": i18n.change.model()}
    main_menu_commands = [
        BotCommand(command=command,
                   description=description) for command,
                   description in commands.items()]
    await bot.set_my_commands(main_menu_commands)