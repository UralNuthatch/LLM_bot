import asyncio
import aiofiles
import aiohttp
import logging
import g4f
from g4f.client import Client
from g4f.cookies import set_cookies

from database.database import DB


logger = logging.getLogger(__name__)


def response_gpt4free_model_text(llm_model, messages: list) -> str:
    client = Client()

    response = client.chat.completions.create(
        model=llm_model,
        messages=messages,
    )

    return response.choices[0].message.content


# Асинхронное скачивание изображения
async def download_img(image_url: str, filename: str) -> None:
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            async with aiofiles.open(filename, "wb") as file:
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    await file.write(chunk)


async def response_gpt4free_model_img(
    model, prompt: str, telegram_id: int, db: DB
) -> str:
    cookies = await db.get_cookies_create_images()
    for cookie in cookies:
        set_cookies(cookie.get("domain"), {cookie.get("name"): cookie.get("value")})

    client = Client()
    response = client.images.generate(
        model=model,
        prompt=prompt,
    )

    images_count = 4
    if model == "gemini-pro":
        images_count = 1

    # Скачиваем файлы на локальную машину
    tasks = [download_img(response.data[i].url, f"{telegram_id}_{i}.png") for i in range(images_count)]
    await asyncio.gather(*tasks)
