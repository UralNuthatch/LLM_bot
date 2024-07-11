import os
import requests
import asyncio
import logging
from aiogram.types import CallbackQuery, FSInputFile
from aiogram_dialog import BaseDialogManager
from fluentogram import TranslatorRunner

from database.database import DB

class NoKeyError(Exception):
    pass

logger = logging.getLogger(__name__)


# Запрос кол-ва кредитов
def balance(key: str):
    response = requests.get("https://api.stability.ai/v1/user/balance",
                            headers={
        "Authorization": f"Bearer {key}"
    })

    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))

    payload = response.json()
    return payload['credits']


# Создать изображение по текстовому запросу
async def response_stability_img_model(text_request: str, telegram_id: int, db: DB):
    # Цена одного запроса в кредитах
    price = 6.5
    key_row = await db.select_valid_key(price)
    if key_row is None:
        raise NoKeyError()

    id, key = key_row
    response = requests.post(
        f"https://api.stability.ai/v2beta/stable-image/generate/sd3",
        headers={
            "authorization": f"Bearer {key}",
            "accept": "image/*"
        },
        files={"none": ''},
        data={
            "model": "sd3-large",  # sd3-large-turbo - 4 credits, sd3-large - 6.5 credits
            "prompt": f"{text_request}",
            "output_format": "png",
        },
    )

    if response.status_code == 200:
        with open(f"./{telegram_id}_0.png", 'wb') as file:
            file.write(response.content)
        # Меняем в базе кол-во оставшихся кредитов для ключа
        await db.waste_credits(id, price)
    else:
        # Если недостаточно кредитов, но в базе неверно число = обновляем
        if 'name' in response.json() and response.json()['name'] == 'payment_required':
            credits = balance(key)
            await db.update_credits(id, credits)
        raise Exception(str(response.json()))


# Найти и заменить
async def response_search_replace_img_model(search_prompt, replace_prompt: str, img, telegram_id: int, db: DB):
    # Цена одного запроса в кредитах
    price = 4
    key_row = await db.select_valid_key(price)
    if key_row is None:
        return 'no_key'

    id, key = key_row
    response = requests.post(
        f"https://api.stability.ai/v2beta/stable-image/edit/search-and-replace",
        headers={
            "authorization": f"Bearer {key}",
            "accept": "image/*"
        },
        files={
            "image": open(img, "rb")
        },
        data={
            "prompt": f"{replace_prompt}",
            "search_prompt": f"{search_prompt}",
            "output_format": "png",
        },
    )


    if response.status_code == 200:
        with open(f"./{telegram_id}.png", 'wb') as file:
            file.write(response.content)
        await db.waste_credits(id, price)
    else:
        # Если недостаточно кредитов, но в базе неверно число = обновляем
        if 'name' in response.json() and response.json()['name'] == 'payment_required':
            credits = balance(key)
            await db.update_credits(id, credits)
        raise Exception(str(response.json()))


# Удалить фон
async def response_remove_background_img_model(img, telegram_id: int, db: DB):
    # Цена одного запроса в кредитах
    price = 3
    key_row = await db.select_valid_key(price)
    if key_row is None:
        return 'no_key'

    id, key = key_row
    response = requests.post(
        f"https://api.stability.ai/v2beta/stable-image/edit/remove-background",
        headers={
            "authorization": f"Bearer {key}",
            "accept": "image/*"
        },
        files={
            "image": open(img, "rb")
        },
        data={
            "output_format": "png"
        },
    )

    if response.status_code == 200:
        with open(f"./{telegram_id}.png", 'wb') as file:
            file.write(response.content)
        await db.waste_credits(id, price)
    else:
        # Если недостаточно кредитов, но в базе неверно число = обновляем
        if 'name' in response.json() and response.json()['name'] == 'payment_required':
            credits = balance(key)
            await db.update_credits(id, credits)
        raise Exception(str(response.json()))


# Улучшение качества изображения
async def response_upscale_img_model(img, prompt: str, telegram_id: int, db: DB) -> tuple[str, str|None]:
    # Цена одного запроса в кредитах
    price = 25
    key_row = await db.select_valid_key(price)
    if key_row is None:
        return 'no_key', None

    id, key = key_row
    response = requests.post(
        f"https://api.stability.ai/v2beta/stable-image/upscale/creative",
        headers={
            "authorization": f"Bearer {key}",
            "accept": "image/*"
        },
        files={
            "image": open(img, "rb")
        },
        data={
            "prompt": prompt,
            "output_format": "png",
        },
    )

    #logging.info(f"Generation ID: {response.json().get('id')}")

    if response.status_code == 200:
        await db.waste_credits(id, price)
        generation_id = response.json().get('id')
        return key, generation_id
    else:
        # Если недостаточно кредитов, но в базе неверно число = обновляем
        if 'name' in response.json() and response.json()['name'] == 'payment_required':
            credits = balance(key)
            await db.update_credits(id, credits)
        #raise Exception(str(response.json()))
        logging.error(str(response.json()))
        return None, None


async def response_upscale_img_result(callback: CallbackQuery, manager: BaseDialogManager,
                                      telegram_id: int, key: str, generation_id: str, i18n: TranslatorRunner):
    try:
        for i in range(1, 25):
            await asyncio.sleep(5)
            await manager.update({"progress": min(i * 10, 100)})
            if i % 2:
                continue
            response = requests.request(
                "GET",
                f"https://api.stability.ai/v2beta/stable-image/upscale/creative/result/{generation_id}",
                headers={
                    'accept': "image/*",  # Use 'application/json' to receive base64 encoded JSON
                    'authorization': f"Bearer {key}"
                },)
            if response.status_code == 202:
                logging.info("Generation in-progress, try again in 10 seconds.")
            elif response.status_code == 200:
                #logging.info("Generation complete!")
                await manager.update({"progress": 100})
                # У бота появляется статус - отправляет фото
                callback.message.bot.send_chat_action(callback.message.chat.id, action="upload_photo")
                with open(f"{telegram_id}.png", 'wb') as file:
                    file.write(response.content)
                    img = FSInputFile(f"{telegram_id}.png")
                # Ограничение на отправку фото в телеграм - 10 мб
                if os.path.getsize(f"{telegram_id}.png") < 10485760:
                    await callback.message.bot.send_photo(telegram_id, img)
                # Отправка в виде файла
                await callback.message.bot.send_document(telegram_id, img)
                os.remove(f"{telegram_id}.png")
                break
            else:
                #raise Exception(str(response.json()))
                logging.error(str(response.json()))
        else:
            callback.message.answer(i18n.error())
    except Exception as ex:
        logging.error(ex)
    finally:
        await manager.done()


# Создать видео
async def response_image_to_video_model(img, telegram_id: int, db: DB) -> tuple[str, str|None]:
    # Цена одного запроса в кредитах
    price = 20
    key_row = await db.select_valid_key(price)
    if key_row is None:
        return 'no_key', None

    id, key = key_row
    response = requests.post(
        f"https://api.stability.ai/v2beta/image-to-video",
        headers={
            "authorization": f"Bearer {key}"
        },
        files={
            "image": open(img, "rb")
        },
        data={
            "seed": 0,
            "cfg_scale": 1.8,
            "motion_bucket_id": 127
        },
    )

    logging.info(f"Generation ID: {response.json().get('id')}")

    if response.status_code == 200:
        await db.waste_credits(id, price)
        generation_id = response.json().get('id')
        return key, generation_id
    else:
        # Если недостаточно кредитов, но в базе неверно число = обновляем
        if 'name' in response.json() and response.json()['name'] == 'payment_required':
            credits = balance(key)
            await db.update_credits(id, credits)
        logging.error(str(response.json()))
        return None, None


async def response_image_to_video_result(callback: CallbackQuery, manager: BaseDialogManager,
                                      telegram_id: int, key: str, generation_id: str, i18n: TranslatorRunner):
    try:
        for i in range(1, 25):
            await asyncio.sleep(5)
            # Каждые пять секунд заполняем прогрессбар на 10%, а запрос отправляем только каждые 10 секунд
            await manager.update({"progress": min(i * 10, 100)})
            if i % 2:
                continue
            response = requests.request(
            "GET",
            f"https://api.stability.ai/v2beta/image-to-video/result/{generation_id}",
            headers={
                'accept': "video/*",  # Use 'application/json' to receive base64 encoded JSON
                'authorization': f"Bearer {key}"
            },)
            if response.status_code == 202:
                logging.info("Generation in-progress, try again in 10 seconds.")
            elif response.status_code == 200:
                #logging.info("Generation complete!")
                await manager.update({"progress": 100})
                # У бота появляется статус - отправляет видео
                callback.message.bot.send_chat_action(callback.message.chat.id, action="upload_video")
                with open(f"{telegram_id}.mp4", 'wb') as file:
                    file.write(response.content)
                    video = FSInputFile(f"{telegram_id}.mp4")
                await callback.message.bot.send_video(telegram_id, video)
                os.remove(f"{telegram_id}.mp4")
                break
            else:
                logging.error(str(response.json()))
        else:
            callback.message.answer(i18n.error())
    except Exception as ex:
        logging.error(ex)
    finally:
        await manager.done()