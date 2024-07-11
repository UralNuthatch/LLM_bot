import os
import logging
import soundfile
import speech_recognition as sr

from aiogram import Bot, Router, F, flags
from aiogram.types import Message, PhotoSize, Voice, FSInputFile
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.utils.chat_action import ChatActionMiddleware
from aiogram_dialog import DialogManager, StartMode
from aiogram.exceptions import TelegramBadRequest
from fluentogram import TranslatorRunner

from config_data.config import load_config, Config
from states import LlmSG, ImgLlmSelectSG
from database.database import DB
from services.model_from_category import select_model_category
from alerts.to_admin import send_no_key
from middlewares.llm_for_user import LLMForUser
from middlewares.history_messages import HistoryMessages
from filters.type_response import TextResponse, ImgResponse
from filters.chat_type import ChatTypeFilter
from filters.draw_filer import DrawWrongModelFilter
from services.models.stability import NoKeyError


# Создаем объект - роутер
router = Router()
# Миддлварь в которой определяются настройки пользователя(выбранная модель)
router.message.outer_middleware(LLMForUser())
# Миддлварь в которой достаются старые сообщения(запросы и ответы) к модели из Redis
router.message.outer_middleware(HistoryMessages())
# Вешаем на роутер миддлварь для отправления статуса "печатает" при ответе
router.message.middleware(ChatActionMiddleware())

# Получаем API-ключ и ключ бота из конфига(через переменные окружения)
config: Config = load_config()

logger = logging.Logger(__name__)


# Этот хэндлер срабатывает на команду start (только в приватных чатах)
@router.message(CommandStart(), ChatTypeFilter("private"))
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


# Хэндлер на команду clear для очистки сохраненных сообщений в Redis для выбранной модели
@router.message(Command(commands="clear"))
async def clear_last_messages(message: Message, i18n: TranslatorRunner, last_messages: list):
    last_messages.clear()
    await message.answer(i18n.cleared.cache())


# Этот хэндлер срабатывает когда приходит звуковое сообщение, а в ответ будет текст (только в приватных чатах)
@router.message(F.voice.as_("voice_prompt"), TextResponse(), ChatTypeFilter("private"))
async def send_audio_text(message: Message, voice_prompt: Voice, bot: Bot, i18n: TranslatorRunner, db: DB, llm: dict, last_messages: list):
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

        await message.answer(f'{llm["llm_img"]} {llm["llm_name"]}:\n{i18n.processing.request()} {text}')

        # Добавляем запрос в последние сообщения
        last_messages.append({"role": "user", "content": str(text)})

        # Обрабатываем запрос в зависимости от модели
        response = await select_model_category(llm["llm_category"], llm["llm_model"], str(text), message.chat.id, db, last_messages)

        # Если длина сообщения больше 4096 - исключение TelegramBadRequest - message too long
        await message.answer(f'{llm["llm_img"]} {llm["llm_name"]}:\n{response[:4050]}')
        if response[4050:]:
            await message.answer(f'{response[4050:]}')
        # Добавляем ответ в последние сообщения чтобы сохранить в Redis
        last_messages.append({"role": "assistant", "content": response})

    # Если parse_mode=Markdown поломан - TelegramBadRequest - can't parse entities...
    except TelegramBadRequest:
        await message.answer(f'{llm["llm_img"]} {llm["llm_name"]}:\n{response[:4050]}', parse_mode='HTML')
        if response[4050:]:
            await message.answer(f'{response[4050:]}', parse_mode='HTML')
        # Добавляем ответ в последние сообщения
        last_messages.append({"role": "assistant", "content": response})

    except Exception as ex:
        # Удаляем последний запрос из последних сообщений, т.к. не получили ответа
        last_messages.pop()
        logging.error(ex)
        await message.answer(f'{llm["llm_img"]} {llm["llm_name"]}:\n{i18n.error()}\n{i18n.clear.cache()}')

    finally:
        # Удаление скачанного ogg и преобразованного в wav файлов
        if os.path.exists(f"{message.chat.id}.ogg"):
            os.remove(f"{message.chat.id}.ogg")
        if os.path.exists(f"{message.chat.id}.wav"):
            os.remove(f"{message.chat.id}.wav")



# Этот хэндлер срабатывает когда приходит звуковое сообщение, а в ответ будет изображение
@router.message(F.voice.as_("voice_prompt"), ImgResponse(), ChatTypeFilter("private"))
@flags.chat_action("upload_photo")
async def send_audio_img(message: Message, voice_prompt: Voice, bot: Bot, i18n: TranslatorRunner, db: DB, llm: dict):
    try:
        # Отправляем статус печатает
        await message.bot.send_chat_action(message.chat.id, "typing")
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

        await message.answer(f'{llm["llm_img"]} {llm["llm_name"]}:\n{i18n.processing.request()} {text}')

        # Обрабатываем запрос в зависимости от модели
        await select_model_category(llm["llm_category"], llm["llm_model"], str(text), message.chat.id, db)

        # 4 изображения
        for i in range(4):
            if os.path.exists(f"{message.chat.id}_{i}.png"):
                img = FSInputFile(f"{message.chat.id}_{i}.png")
                if os.path.getsize(f"{message.chat.id}_{i}.png") < 10485760:
                    await message.answer_photo(img)
                else:
                    await message.answer_document(img)
                os.remove(f"{message.chat.id}_{i}.png")
    # Если закончились ключи
    except NoKeyError:
        await message.answer(i18n.keys.ended())
        await send_no_key(bot)
    # Обрабатываем другие ошибки
    except Exception as ex:
        logging.error(ex)
        await message.answer(f'{llm["llm_img"]} {llm["llm_name"]}:\n{i18n.error()}')

    finally:
        # Удаление скачанного ogg и преобразованного в wav файлов
        if os.path.exists(f"{message.chat.id}.ogg"):
            os.remove(f"{message.chat.id}.ogg")
        if os.path.exists(f"{message.chat.id}.wav"):
            os.remove(f"{message.chat.id}.wav")


# Этот хэндлер будет обрабатывать изображения от пользоваетеля с подписью или без
@router.message(F.photo[-1].as_("largest_photo"), ChatTypeFilter("private"))
async def get_send_photo(message: Message, largest_photo: PhotoSize, dialog_manager:DialogManager, i18n: TranslatorRunner):
        # Если изображение от пользователя пришло без подписи, то ставим стандартный запрос
        if message.caption:
            text = message.caption
        else:
            text = i18n.picture.response()

        # Получаем путь до изображения
        file = await message.bot.get_file(file_id=largest_photo.file_id)
        img_path = f"input_{message.chat.id}.jpeg"
        # Скачиваем файл на локальную машину
        await message.bot.download_file(file_path=file.file_path, destination=img_path)
        await dialog_manager.start(state=ImgLlmSelectSG.start, mode=StartMode.RESET_STACK, data={'img': img_path, 'text': text})


# Если пользователь прислал текстовое сообщение, а ответ будет изображение
@router.message(F.text, ImgResponse(), ChatTypeFilter("private"))
@router.message(F.text, TextResponse(), DrawWrongModelFilter(), ChatTypeFilter("private"))
@router.message(Command(commands=["bot", "бот"]), ImgResponse(), ChatTypeFilter(["group", "supergroup"]))
@router.message(Command(commands=["bot", "бот"]), TextResponse(), DrawWrongModelFilter(), ChatTypeFilter(["group", "supergroup"]))
@flags.chat_action("upload_photo")
async def text_for_image(message: Message, bot: Bot, i18n: TranslatorRunner, db: DB, llm: dict):
    try:
        text = message.text
        # Для групповых чатов
        if message.chat.type != "private":
            text = text.lstrip("/bot").lstrip("/бот")
        # Если выбрана текстовая модель, а пользователь начал свой запрос с "нарисуй"
        if await DrawWrongModelFilter()(message=message, llm=llm):
            # Выберем какую-то img-модель по-умолчанию
            model = "dall-e-3"
            llm_category, llm_model, llm_name, llm_img, llm_response = await db.get_data_from_model(model)
            llm['llm_category'] = llm_category
            llm['llm_model'] = llm_model
            llm['llm_name'] = llm_name
            llm['llm_img'] = llm_img
            llm['llm_response'] = llm_response

        # Обрабатываем запрос в зависимости от модели
        await select_model_category(llm["llm_category"],
                                               llm["llm_model"],
                                               text,
                                               message.chat.id,
                                               db)
        # 4 изображения
        for i in range(4):
            if os.path.exists(f"{message.chat.id}_{i}.png"):
                img = FSInputFile(f"{message.chat.id}_{i}.png")
                if os.path.getsize(f"{message.chat.id}_{i}.png") < 10485760:
                    await message.answer_photo(img)
                else:
                    await message.answer_document(img)
                os.remove(f"{message.chat.id}_{i}.png")
    # Если закончились ключи
    except NoKeyError:
        if message.chat.type == "private":
            await message.answer(i18n.keys.ended())
        await send_no_key(bot)
    # Обрабатываем другие ошибки
    except Exception as ex:
        logging.error(ex)
        await message.answer(f'{llm["llm_img"]} {llm["llm_name"]}:\n{i18n.error()}')


# Если пользователь прислал текстовое сообщение, и ответ тоже текст
@router.message(F.text, TextResponse(), ChatTypeFilter("private"))
@router.message(Command(commands=["bot", "бот"]), TextResponse(), ChatTypeFilter(["group", "supergroup"]))
async def text_for_text(message: Message, i18n: TranslatorRunner, db: DB, llm: dict, last_messages: list):
    try:
        text = message.text
        # Для групповых чатов
        if message.chat.type != "private":
            text = text.lstrip("/bot").lstrip("/бот")
        # Отправляем статус печатает
        await message.bot.send_chat_action(message.chat.id, "typing")
        # Добавляем запрос в последние сообщения
        last_messages.append({"role": "user", "content": text})
        # Обрабатываем запрос в зависимости от модели
        response = await select_model_category(llm["llm_category"],
                                               llm["llm_model"],
                                               text,
                                               message.chat.id,
                                               db,
                                               last_messages)

        # Если длина сообщения больше 4096 - исключение TelegramBadRequest - message too long
        await message.answer(f'{llm["llm_img"]} {llm["llm_name"]}:\n{response[:4050]}')
        if response[4050:]:
            await message.answer(f'{response[4050:]}')
        # Добавляем ответ в последние сообщения
        last_messages.append({"role": "assistant", "content": response})
    # Если parse_mode=Markdown поломан - TelegramBadRequest - can't parse entities...
    except TelegramBadRequest:
        await message.answer(f'{llm["llm_img"]} {llm["llm_name"]}:\n{response[:4050]}', parse_mode='HTML')
        if response[4050:]:
            await message.answer(f'{response[4050:]}', parse_mode='HTML')
        # Добавляем ответ в последние сообщения
        last_messages.append({"role": "assistant", "content": response})
    except Exception as ex:
        # Удаляем последний запрос из последних сообщений, т.к. не получили ответа
        last_messages.pop()
        logging.error(ex)
        await message.answer(f'{llm["llm_img"]} {llm["llm_name"]}:\n{i18n.error()}\n{i18n.clear.cache()}')



# Команда для анализа последних сообщений в чате группы:
# /history 100 Дополнительные условия
# 100 - messages_count - кол-во последних соощений для анализа
# Дополнительные условия - add_text - любой свой запрос дополнительно
# команда может быть в сокращенном виде: /history; /history 50; /history кто отправил больше всех сообщений?;
@router.message(Command(commands=["history", "история"]))
async def history_analysis(message: Message, command: CommandObject, i18n: TranslatorRunner, db: DB, llm: dict, last_messages: list, history: list):
    try:
        messages_count = 100
        # add_text - дополнительный запрос
        add_text = ""
        text = "Проанализируй историю сообщений из чата и выдели самое главное. "
        if not command.args is None:
            commands = command.args.split(" ", maxsplit=1)
            if commands[0].isdigit():
                messages_count = int(commands[0])
                if len(commands) > 1:
                    add_text = commands[1]
            else:
                add_text = " ".join(commands)
        # Собираем вместе весь запрос для анализа истории чата + доп. запрос + сама история чата
        text = text + add_text + " Чат: " + "\n\n".join(history[:messages_count])
        #request_text = [{"role": "user", "content": text}]

        # Отправляем статус печатает
        await message.bot.send_chat_action(message.chat.id, "typing")
        # Очищаем последние сообщения
        last_messages.clear()
        # Добавляем запрос в последние сообщения
        last_messages.append({"role": "user", "content": text})

        # Обрабатываем запрос в зависимости от модели
        response = await select_model_category(llm["llm_category"],
                                               llm["llm_model"],
                                               "",
                                               message.chat.id,
                                               db,
                                               last_messages)

        # Если длина сообщения больше 4096 - исключение TelegramBadRequest - message too long
        await message.answer(f'{llm["llm_img"]} {llm["llm_name"]}:\n{response[:4050]}')
        if response[4050:]:
            await message.answer(f'{response[4050:]}')
        # Добавляем ответ в последние сообщения
        last_messages.append({"role": "assistant", "content": response})

    # Если parse_mode=Markdown поломан - TelegramBadRequest - can't parse entities...
    except TelegramBadRequest:
        await message.answer(f'{llm["llm_img"]} {llm["llm_name"]}:\n{response[:4050]}', parse_mode='HTML')
        if response[4050:]:
            await message.answer(f'{response[4050:]}', parse_mode='HTML')
        # Добавляем ответ в последние сообщения
        last_messages.append({"role": "assistant", "content": response})

    except Exception as ex:
        # Удаляем последний запрос из последних сообщений, т.к. не получили ответа
        last_messages.pop()
        logging.error(ex)
        await message.answer(f'{llm["llm_img"]} {llm["llm_name"]}:\n{i18n.error()}\n{i18n.clear.cache()}')