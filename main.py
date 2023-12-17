import logging
from aiogram import Bot, Dispatcher
from config_data.config import load_config, Config
from handlers import user_handlers, other_handlers
from keyboards.set_menu import set_main_menu

# Получаем API-ключ и ключ бота из конфига(через переменные окружения)
config: Config = load_config()

# Создаем объекты бота и диспетчера
bot = Bot(token=config.tgbot.token)
dp = Dispatcher()

# Регистрируем роутеры в диспетчере
dp.include_router(user_handlers.router)
dp.include_router(other_handlers.router)


# Конфигурируем и запускаем логирование
logger = logging.basicConfig(
                            format='%(filename)s:%(lineno)d #%(levelname)-8s '
                            '[%(asctime)s] - %(name)s - %(message)s',
                            level=logging.INFO
                            )
logging.info("Starting bot...")

# Регистрируем асинхронную функцию в диспетчере,
# которая будет выполняться на старте бота
dp.startup.register(set_main_menu)

# Запускаем бота на long-polling
dp.run_polling(bot)
