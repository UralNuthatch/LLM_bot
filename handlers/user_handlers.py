import os
import logging
import requests
import soundfile
import speech_recognition as sr
import google.generativeai as genai
from aiogram import Router, F
from aiogram.types import Message, PhotoSize, Voice
from aiogram.filters import CommandStart, Command
from config_data.config import load_config, Config
from PIL import Image
from lexicon.lexicon import LEXICON

# Создаем объект - роутер
router = Router()

# Получаем API-ключ и ключ бота из конфига(через переменные окружения)
config: Config = load_config()

genai.configure(api_key=config.api_key)


# Этот хэндлер срабатывает на команду start
@router.message(CommandStart())
async def process_start_command(message: Message):
    text = LEXICON["/start"]
    try:
        file_id = "AgACAgIAAxkBAAIFUWV65ZX6qF_21NsZnMzZ_rw1-WWPAAKP0TEbFd3YS9XO5YHx7CH6AQADAgADeAADMwQ"
        await message.answer_photo(file_id, caption=text)
    except:
        await message.answer(text)


# Этот хэндлер будет срабатывать на комнаду help
@router.message(Command(commands="help"))
async def process_help_command(message: Message):
    await message.answer(LEXICON["/help"])


# Этот хэндлер срабатывает когда приходит звуковое сообщение
@router.message(F.voice.as_("voice_prompt"))
async def get_send_audio(message: Message, voice_prompt: Voice, bot):
    try:
        logging.info("Начало обработки аудиозапроса")
        # У бота появляется статус - печатает
        await bot.send_chat_action(message.chat.id, action="typing")
        # Скачивание файла в ogg формате
        file = await bot.get_file(voice_prompt.file_id)
        file_path = file.file_path
        await bot.download_file(file_path, f"{message.chat.id}.ogg")
        logging.info("Скачал файл из телеграма в ogg формате")

        # Конвертация в wav формат
        data, samplerate = soundfile.read(f"{message.chat.id}.ogg")
        soundfile.write(f"{message.chat.id}.wav", data, samplerate)
        logging.info("Файл сконвертирован в wav формат")


        recognizer = sr.Recognizer()
        with sr.AudioFile(f"{message.chat.id}.wav") as source:
            audio = recognizer.record(source=source)

        # Преобразование аудиозаписи в текст
        text = recognizer.recognize_google(audio, language="ru-RU")
        logging.info("Голосовой файл преобразован в текст, отправляю запрос модели gemini")

        await message.answer(f"{LEXICON['processing_response']} {text}")
        # У бота появляется статус - печатает
        await bot.send_chat_action(message.chat.id, action="typing")
        # Отправляем модели текстовый запрос
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(text)
        logging.info("Получен ответ от gemini. Отправляю ответ пользователю")
        await message.answer(response.text)

    except Exception as ex:
        await message.answer(LEXICON["error"])
        logging.error(ex)
    finally:
        # Удаление скачанного ogg и преобразованного в wav файлов
        if os.path.exists(f"{message.chat.id}.ogg"):
            os.remove(f"{message.chat.id}.ogg")
        if os.path.exists(f"{message.chat.id}.wav"):
            os.remove(f"{message.chat.id}.wav")



# Этот хэндлер будет обрабатывать изображения от пользоваетеля с подписью или без
@router.message(F.photo[-1].as_('largest_photo'))
async def get_send_photo(message: Message, largest_photo: PhotoSize, bot):
    try:
        # У бота появляется статус - печатает
        await bot.send_chat_action(message.chat.id, action="typing")
        # Используется модель поддерживающая изображения и текст в запросах
        model = genai.GenerativeModel('gemini-pro-vision')
        # Если изображение от пользователя пришло без подписи, то ставим стандартный запрос
        if message.caption:
            text = message.caption
        else:
            text = LEXICON["picture_response"]
        # Получаем путь до изображения
        file = await bot.get_file(file_id=largest_photo.file_id)
        file_path = f"https://api.telegram.org/file/bot{config.tgbot.token}/{file.file_path}"
        img_response = requests.get(file_path, stream=True).raw

        await bot.send_chat_action(message.chat.id, action="typing")
        # Отправляем запрос с картинкой и текстом модели ИИ
        with Image.open(img_response) as img:
            response = model.generate_content([text, img], stream=True)
        response.resolve()
        await message.answer(text=response.text)

    # Обрабатываем ошибки и заносим в логи
    except Exception as ex:
        logging.error(ex)
        await message.answer(LEXICON["error"])


# Этот хэндлер срабатывает если пользователь прислал текстовое сообщение
@router.message(F.text)
async def get_send_text(message: Message, bot):
    try:
        # У бота появляется статус - печатает
        await bot.send_chat_action(message.chat.id, action="typing")
        # Используем модель предназначенную только для текстовых запросов
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(message.text)
        await message.answer(response.text)
    # Обрабатываем возможные ошибки
    except Exception as ex:
        logging.error(ex)
        await message.answer(LEXICON["error"])