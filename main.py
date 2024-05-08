import logging
import asyncio
import nest_asyncio
from asyncpg import create_pool
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram_dialog import setup_dialogs
from fluentogram import TranslatorHub
from redis import Redis
from config_data.config import load_config, Config
from handlers import user_handlers, other_handlers, llm_dialog, active_users, admin_handlers, img_llm_dialog
from keyboards.set_menu import set_main_menu
from middlewares.db import DbSessionMiddleware
from middlewares.i18n import TranslatorRunnerMiddleware
from utils.i18n import create_translator_hub


async def main():
    # Получаем API-ключ и ключ бота из конфига(через переменные окружения)
    config: Config = load_config()

    # Создаем объекты бота и диспетчера
    bot = Bot(token=config.tgbot.token, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp = Dispatcher()

    # Создаем объект типа TranslatorHub
    translator_hub: TranslatorHub = create_translator_hub()
    dp.workflow_data.update({'_translator_hub': translator_hub})

    # Создаем пул соединений к БД
    pool = await create_pool(database=config.db.database, host=config.db.db_host, user=config.db.db_user, password=config.db.db_password)

    # Добавляем пул соединений с БД в диспетчер
    dp.workflow_data.update({'pool': pool})

    # Создаем Redis и добавляем в диспетчер
    redis = Redis(host=config.redis.redis_host, port=config.redis.redis_port, db=config.redis.redis_db)
    dp.workflow_data.update({'redis': redis})

    # Регистрируем роутеры в диспетчере
    dp.include_router(llm_dialog.llm_dialog)
    dp.include_router(img_llm_dialog.img_llm_select_dialog)
    dp.include_router(img_llm_dialog.img_llm_dialog_google)
    dp.include_router(img_llm_dialog.img_llm_dialog_sd3)
    dp.include_router(img_llm_dialog.progress_bar)
    dp.include_router(admin_handlers.router)
    dp.include_router(admin_handlers.keys_dialog)
    dp.include_router(user_handlers.router)
    setup_dialogs(dp)
    dp.include_router(active_users.router)
    dp.include_router(other_handlers.router)

    # Регистрируем миддлварь для i18n
    dp.update.middleware(TranslatorRunnerMiddleware())

    # Регистрируем миддлварь для БД
    dp.update.middleware(DbSessionMiddleware())

    # Конфигурируем и запускаем логирование
    logger = logging.getLogger("LLM_bot_main")
    logging.basicConfig(
                                format='[{asctime}] #{levelname:8} {filename}:'
                                        '{lineno} - {name} - {message}',
                                style='{',
                                level=logging.WARNING)
    logger.warning("Starting bot...")

    # Регистрируем асинхронную функцию в диспетчере,
    # которая будет выполняться на старте бота
    dp.startup.register(set_main_menu)

    # Запускаем бота на long-polling
    await dp.start_polling(bot, _translator_hub=translator_hub)

if __name__ == '__main__':
    nest_asyncio.apply()
    asyncio.run(main())
