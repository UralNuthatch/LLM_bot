import os
import asyncio
import logging
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from aiogram.types import Message, FSInputFile

from database.database import DB


def get_options():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    # options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("start-maximized")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)
    # Указываем директорию для скачивания файлов
    preferences = {
        "download.default_directory": os.path.join(os.getcwd(), "downloads_luma")
    }
    options.add_experimental_option("prefs", preferences)
    return options


async def get_video_from_text(login, password, text_response, message: Message, pool):
    try:
        print("enter generate")
        options = get_options()
        driver = webdriver.Chrome(options=options)
        print("create driver")
        driver.get("https://lumalabs.ai/dream-machine/creations")

        wait = WebDriverWait(driver, 10, 1)
        # Логин в аккаунт google
        BTN_SIGN_UP_WITH_GOOGLE = ("xpath", '//a[contains(@class, "w-max")]')
        wait.until(EC.element_to_be_clickable(BTN_SIGN_UP_WITH_GOOGLE)).click()

        INPUT_EMAIL = ("xpath", '//*[@id="identifierId"]')
        wait.until(EC.visibility_of_element_located(INPUT_EMAIL)).send_keys(login)
        BTN_NEXT_EMAIL = ("xpath", '//div[contains(@class, "O1Slxf")]//button')
        wait.until(EC.element_to_be_clickable(BTN_NEXT_EMAIL)).click()

        INPUT_PASSWORD = ("xpath", '//input[@type="password"]')
        wait.until(EC.visibility_of_element_located(INPUT_PASSWORD)).send_keys(password)
        BTN_NEXT_PASSWORD = ("xpath", '//*[@id="passwordNext"]/div/button')
        wait.until(EC.element_to_be_clickable(BTN_NEXT_PASSWORD)).click()

        await asyncio.sleep(5)
        if not driver.current_url.startswith("https://luma"):
            BTN_NEXT_SIGN = ("xpath", '//button[./span[text()="Продолжить"]]')
            wait.until(EC.element_to_be_clickable(BTN_NEXT_SIGN)).click()
        print("enter luma")
        GENERATIONS_LEFT = ("xpath", '//strong[@class="font-medium"]')
        gen_left = wait.until(EC.visibility_of_element_located(GENERATIONS_LEFT)).text
        
        # Получение соединения из пула
        async with pool.acquire() as connection:
            # Открытие транзакции
            async with connection.transaction():
                db = DB(connection=connection)
                # Обновляем кол-во оставшихся попыток
                await db.update_left_responses_all(login, max(0, int(gen_left) - 1))

        if gen_left == "0":
            raise Exception(f"Account {login} have 0 generations left")
        print("left responses")
        # Вводим запрос и нажимаем кнопку генерации видео
        response = ("xpath", '//textarea[contains(@class, "placeholder")]')
        wait.until(EC.visibility_of_element_located(response)).send_keys(text_response)
        btn_response = ("xpath", '//button[contains(@class, "relative size")]')
        wait.until(EC.element_to_be_clickable(btn_response)).click()
        print("start generate video from response")
        await asyncio.sleep(15)

        BTN_DOWNLOAD = ("xpath", "(//div[@class='flex flex-col gap-2'])[1]//button[@title='Download']")
        for _ in range(120):
            try:
                await asyncio.sleep(30)
                print("in cycle")
                driver.find_element(*BTN_DOWNLOAD)
                driver.refresh()
                driver.find_element(*BTN_DOWNLOAD).click()
                print("download video")
                asyncio.sleep(15)
                break
            except:
                pass
        else:
            logging.error("10 min not enough to generate this video")
            return
        print("try send video")
        for file in os.listdir("downloads_luma"):
            if text_response[:5] in file:
                await message.bot.send_chat_action(message.chat.id, action="upload_video")
                video = FSInputFile(f"downloads_luma/{file}")
                await message.answer_video(video)
                os.remove(f"downloads_luma/{file}")
        print("finish")

    except Exception as ex:
        logging.error(ex)
        await message.answer(f"Произошла ошибка во время генерации видео по запросу: {text_response}")
    finally:
        # Получение соединения из пула
        async with pool.acquire() as connection:
            # Открытие транзакции
            async with connection.transaction():
                db = DB(connection=connection)
                # Освобождаем аккаунт, меняя статус на '0' в БД
                await db.change_luma_working_now(login, "0")