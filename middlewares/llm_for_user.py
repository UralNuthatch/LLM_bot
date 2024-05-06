import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from fluentogram import TranslatorHub
from database.database import DB


logger = logging.getLogger(__name__)


# Определение модели пользователя из Базы Данных
class LLMForUser(BaseMiddleware):
    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: Dict[str, Any]) -> Any:
        user: User = data.get('event_from_user')
        if user is None:
            # Дефолтные настройки пользователя
            data['llm'] = {'llm_category': 1,
                           'llm_model': 'gemini-pro',
                           'llm_name': 'gemini-1.0',
                           'llm_img': '🅖',
                           'llm_response': 'text'}
            return await handler(event, data)

        db: DB = data['db']
        llm_category, llm_model, llm_name, llm_img, llm_response = await db.get_users_llm(user.id)
        data['llm'] = {'llm_category': llm_category,
                       'llm_model': llm_model,
                       'llm_name': llm_name,
                       'llm_img': llm_img,
                       'llm_response': llm_response}

        return await handler(event, data)