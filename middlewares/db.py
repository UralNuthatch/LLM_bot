import logging
from typing import Callable, Awaitable, Dict, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from asyncpg import Pool
from database.database import DB


logger = logging.getLogger(__name__)

class DbSessionMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]) -> Any:

        pool: Pool = data['pool']
        
        # Получение соединения из пула
        async with pool.acquire() as connection:
            # Открытие транзакции
            async with connection.transaction():
                db = DB(connection=connection)
                data['db'] = db
                return await handler(event, data)
