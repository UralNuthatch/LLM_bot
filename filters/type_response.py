from aiogram.filters import Filter
from aiogram.types import Message


class ImgResponse(Filter):
    async def __call__(self, message: Message, llm=None):
        return llm.get("llm_response") == "img"


class TextResponse(Filter):
    async def __call__(self, message: Message, llm=None):
        return llm.get("llm_response") == "text"