import logging
import json
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User


logger = logging.getLogger(__name__)


class HistoryMessages(BaseMiddleware):
    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: Dict[str, Any]) -> Any:
        # В Redis последние сообщения будут храниться в виде:
        # 123456789_messages_gpt-4: [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "Hello. How I can help you?"}, ...]
        # 123456789 - telegram_id
        # gpt-4 - llm_model

        # Сколько последних сообщений хранится.Пример: 10 = 5 запросов + 5 ответов
        MAX_COUNT_MESSAGES = 10

        try:
            user: User = data.get('event_from_user')
            llm_model = data['llm']["llm_model"]

            user_llm_key = f"{str(user.id)}_messages_{llm_model}"

            last_messages = data["redis"].get(user_llm_key)

            # Если старых сообщений нет
            if last_messages is None:
                last_messages = []
            else:
                # В Redis список сообщений хранится в json формате
                last_messages = json.loads(last_messages)
            
            data["last_messages"] = last_messages

        except Exception as ex:
            data["last_messages"] = []
            logging.error(ex)

        await handler(event, data)

        # Обрезаем первые сообщение если их больше чем должно храниться и переводим в json
        last_messages = json.dumps(last_messages[-MAX_COUNT_MESSAGES:])
        # Добавляем в Redis
        data["redis"].set(user_llm_key, last_messages)