import os
import logging
import soundfile
import speech_recognition as sr

from aiogram import Bot, Router, F, flags
from aiogram.types import Message, PhotoSize, Voice, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.utils.chat_action import ChatActionMiddleware
from aiogram_dialog import DialogManager, StartMode
from fluentogram import TranslatorRunner

from config_data.config import load_config, Config
from states import LlmSG, ImgLlmSelectSG
from database.database import DB
from services.model_from_category import select_model_category
from alerts.to_admin import send_no_key


# Создаем объект - роутер
router = Router()
# Вешаем на роутер миддлварь для отправления статуса "печатает" при ответе
router.message.middleware(ChatActionMiddleware())

# Получаем API-ключ и ключ бота из конфига(через переменные окружения)
config: Config = load_config()

logger = logging.Logger(__name__)


# Этот хэндлер срабатывает на команду start
@router.message(CommandStart())
async def process_start_command(message: Message):
    try:
        img = FSInputFile(f"start.png")
        await message.answer_photo(img)
    except:
        await message.answer("Hello, can I help you?")


# Этот хэндлер будет срабатывать на комнаду models
@router.message(Command(commands="models"))
async def process_help_command(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=LlmSG.start, mode=StartMode.RESET_STACK)


# Этот хэндлер срабатывает когда приходит звуковое сообщение
@router.message(F.voice.as_("voice_prompt"))
async def get_send_audio(message: Message, voice_prompt: Voice, bot: Bot, i18n: TranslatorRunner, db: DB):
    try:
        # Скачивание файла в ogg формате
        file = await bot.get_file(voice_prompt.file_id)
        file_path = file.file_path
        await bot.download_file(file_path, f"{message.chat.id}.ogg")

        # Конвертация в wav формат
        data, samplerate = soundfile.read(f"{message.chat.id}.ogg")
        soundfile.write(f"{message.chat.id}.wav", data, samplerate)

        recognizer = sr.Recognizer()
        with sr.AudioFile(f"{message.chat.id}.wav") as source:
            audio = recognizer.record(source=source)

        # Преобразование аудиозаписи в текст
        text = recognizer.recognize_google(audio, language="ru-RU")

        await message.answer(f"{i18n.processing.request()} {text}")

        # Определяем по БД модель ИИ пользователя
        llm_category, llm_model, llm_name, llm_img = await db.get_users_llm(message.from_user.id)
        # Обрабатываем запрос в зависимости от модели
        response = await select_model_category(llm_category, llm_model, str(text), message.from_user.id, db)
        # Если был запрос на генерацию изображения
        if response == 'image':
            if os.path.exists(f"{message.chat.id}.jpeg"):
                img = FSInputFile(f"{message.chat.id}.jpeg")
                await message.answer_photo(img)
                os.remove(f"{message.chat.id}.jpeg")
        elif response == 'no_key':
            await message.answer("К сожалению закончились попытки генерации изображений. Попробуйте позднее.")
            await message.bot.send_message(chat_id=348123497, text='закончились ключи для stability')
        else:
            await message.answer(f"{llm_img} {llm_name}:\n{response}")

    except Exception as ex:
        await message.answer(i18n.error())
        logging.error(ex)
    finally:
        # Удаление скачанного ogg и преобразованного в wav файлов
        if os.path.exists(f"{message.chat.id}.ogg"):
            os.remove(f"{message.chat.id}.ogg")
        if os.path.exists(f"{message.chat.id}.wav"):
            os.remove(f"{message.chat.id}.wav")


# Этот хэндлер будет обрабатывать изображения от пользоваетеля с подписью или без
@router.message(F.photo[-1].as_("largest_photo"))
async def get_send_photo(message: Message, largest_photo: PhotoSize, dialog_manager:DialogManager, i18n: TranslatorRunner):
        # Если изображение от пользователя пришло без подписи, то ставим стандартный запрос
        if message.caption:
            text = message.caption
        else:
            text = i18n.picture.response()

        # Получаем путь до изображения
        file = await message.bot.get_file(file_id=largest_photo.file_id)
        img_path = f"input_{message.from_user.id}.jpeg"
        # Скачиваем файл на локальную машину
        await message.bot.download_file(file_path=file.file_path, destination=img_path)
        await dialog_manager.start(state=ImgLlmSelectSG.start, mode=StartMode.RESET_STACK, data={'img': img_path, 'text': text})


# Этот хэндлер срабатывает если пользователь прислал текстовое сообщение
@router.message(F.text)
async def get_send_text(message: Message, bot: Bot, i18n: TranslatorRunner, db: DB):
    try:
        # Определяем по БД модель ИИ пользователя
        llm_category, llm_model, llm_name, llm_img = await db.get_users_llm(message.from_user.id)
        # Обрабатываем запрос в зависимости от модели
        response = await select_model_category(llm_category, llm_model, message.text, message.from_user.id, db)
        # Если был запрос на генерацию изображения
        if response == 'image':
            if os.path.exists(f"{message.chat.id}.png"):
                # У бота появляется статус - загрузка фотографии
                await message.bot.send_chat_action(message.chat.id, action="upload_photo")
                img = FSInputFile(f"{message.chat.id}.png")
                if os.path.getsize(f"{message.chat.id}.png") < 10485760:
                    await message.answer_photo(img)
                await message.answer_document(img)
                os.remove(f"{message.chat.id}.png")
        elif response == 'no_key':
            await message.answer(i18n.keys.ended())
            await send_no_key(bot)
        else:
            # Если был текстовый запрос и тоже в виде текста
            await message.answer(f"{llm_img} {llm_name}:\n{response}")
    # Обрабатываем возможные ошибки
    except Exception as ex:
        logging.error(ex)
        await message.answer(f"{llm_img} {llm_name}:\n{i18n.error()}")
