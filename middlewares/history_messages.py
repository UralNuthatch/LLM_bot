import logging
import json
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User, Message, Chat


logger = logging.getLogger(__name__)


class HistoryMessages(BaseMiddleware):
    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: Dict[str, Any]) -> Any:
        # В Redis последние сообщения будут храниться в виде:
        # 123456789_messages_gpt-4: [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "Hello. How I can help you?"}, ...]
        # 123456789 - telegram_id
        # gpt-4 - llm_model
        # Updated 05.07.2024 -> 123456789_messages_all

        # Сколько последних сообщений хранится.Пример: 10 = 5 запросов + 5 ответов
        MAX_COUNT_MESSAGES = 6


        # Для групп будет сохраняться история текстовых сообщений в виде:
        # 123456789_history: ["Сообщение_1", "Сообщение_2", ..., "Сообщение_n"]
        # 123456789 - chat.id группы/супергруппы

        # Сколько последних сообщений истории группы хранится
        MAX_COUNT_HISTORY = 100

        try:
            chat: Chat = data.get('event_chat')
            #llm_model = data['llm']["llm_model"]
            llm_model = "all"

            user_llm_key = f"{str(chat.id)}_messages_{llm_model}"

            last_messages = data["redis"].get(user_llm_key)

            # Если старых сообщений нет
            if last_messages is None:
                last_messages = []
            else:
                # В Redis список сообщений хранится в json формате
                last_messages = json.loads(last_messages)

            data["last_messages"] = last_messages

            # Для групп и супергрупп (история сообщений)
            if chat.type != "private":
                if not data.get('event_update').message.text.startswith("/") or data.get('event_update').message.text.startswith("/history") or data.get('event_update').message.text.startswith("/история"):
                    history_key = f"{str(chat.id)}_history"
                    history = data["redis"].get(history_key)
                    # Если истории пока нет
                    if history is None:
                        history = []
                    else:
                        # В Redis список сообщений хранится в json формате
                        history = json.loads(history)

                    if not data.get('event_update').message.text.startswith("/history") and not data.get('event_update').message.text.startswith("/история"):
                        # Сразу добавим новое сообщение в историю
                        new_message = "Пользователь: " + data.get('event_update').message.from_user.username + "\n" + "Сообщение: " + data.get('event_update').message.text
                        history.append(new_message)

                    data["history"] = history


        except Exception as ex:
            data["last_messages"] = []
            data["history"] = []
            logging.error(ex)

        await handler(event, data)

        # Обрезаем первые сообщение если их больше чем должно храниться и переводим в json
        last_messages = json.dumps(last_messages[-MAX_COUNT_MESSAGES:])
        # Добавляем в Redis
        data["redis"].set(user_llm_key, last_messages)


        # Для групп и супергрупп (история сообщений)
        if chat.type != "private":
            if not data.get('event_update').message.text.startswith("/"):
                history = json.dumps(history[-MAX_COUNT_HISTORY:])
                # Добавляем в Redis
                data["redis"].set(history_key, history)