from aiogram.filters import Filter
from aiogram.types import Message


class DrawWrongModelFilter(Filter):
    async def __call__(self, message: Message, llm=None):
        text = message.text
        if llm.get("response") != "img" and (text.startswith("нарисуй") or text.startswith("Нарисуй")
                                             or text.startswith("НАРИСУЙ") or text.startswith("draw")
                                             or text.startswith("Draw") or text.startswith("DRAW")
                                             or text.startswith("/бот нарисуй") or text.startswith("/бот Нарисуй")
                                             or text.startswith("/бот НАРИСУЙ") or text.startswith("/bot draw")
                                             or text.startswith("/bot Draw") or text.startswith("/bot DRAW")
                                             or text.startswith("/bot нарисуй") or text.startswith("/бот draw")):
            return True
        return False