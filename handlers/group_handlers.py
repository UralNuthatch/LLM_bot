from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from aiogram.utils.chat_action import ChatActionMiddleware

from middlewares.llm_for_user import LLMForUser
from middlewares.history_messages import HistoryMessages
from filters.chat_type import ChatTypeFilter



router = Router()
# Миддлварь в которой определяются настройки пользователя(выбранная модель)
router.message.outer_middleware(LLMForUser())
# Миддлварь в которой достаются старые сообщения(запросы и ответы) к модели из Redis
router.message.outer_middleware(HistoryMessages())
# Вешаем на роутер миддлварь для отправления статуса "печатает" при ответе
router.message.middleware(ChatActionMiddleware())
# Фильтр на роутер - только групповые чаты
router.message.filter(ChatTypeFilter(["group", "supergroup"]))


# Команда для анализа последних сообщений в чате группы:
# /history 100 Дополнительные условия
# 100 - кол-во последних соощений для анализа
# Дополнительные условия - любой свой запрос дополнительно
# команда может быть в сокращенном виде: /history; /history 50; /history кто отправил больше всех сообщений?;
@router.message(Command(commands="history"))
async def history_analysis(message: Message, command: CommandObject):
    messages_count = 100
    add_text = "Ещё "
    print("Проанализируй историю сообщений из чата и выдели самое главное. ")
    if not command.args is None:
        commands = command.args.split(" ", maxsplit=1)
        if commands[0].isdigit():
            messages_count = int(commands[0])
            if len(commands) > 1:
                add_text = commands[1]
        else:
            add_text = " ".join(commands)
    print(messages_count)
    print(add_text)