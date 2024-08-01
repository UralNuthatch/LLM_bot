import requests
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


async def response_gpt4free_model_img(model, prompt: str, telegram_id: int, db: DB) -> str:
    cookies = await db.get_cookies_create_images()
    for cookie in cookies:
        set_cookies(
            cookie.get("domain"),
            {
                cookie.get("name"): cookie.get("value")
            })

    client = Client()
    response = client.images.generate(
        model=model,
        prompt=prompt,
    )

    imgages_count = 4
    if model == "gemini-pro":
        imgages_count = 1

    # Скачиваем файлы на локальную машину
    for i in range(imgages_count):
        image_url = response.data[i].url
        img_data = requests.get(image_url)
        with open(f"{telegram_id}_{i}.png", "wb") as file:
            file.write(img_data.content)
