import os
import asyncio
import logging
from PIL import Image
from aiogram_dialog import Dialog, Window, DialogManager, ShowMode
from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.text import Const, Format, Progress, Multi
from aiogram_dialog.widgets.input import TextInput, MessageInput, ManagedTextInput
from aiogram_dialog.widgets.kbd import Button, Next, Row, Column
from aiogram.types import Message, FSInputFile
from fluentogram import TranslatorRunner

from states import ImgLlmGoogleSG, ImgLlmSD3SG, ImgLlmSelectSG, ProgressSG
from database.database import DB
from services.models.google import response_google_model_for_image
from alerts.to_admin import send_no_key
from services.models.stability import (response_search_replace_img_model, response_remove_background_img_model,
                                       response_image_to_video_model, response_upscale_img_model,
                                       response_upscale_img_result, response_image_to_video_result)


logger = logging.getLogger(__name__)


async def select_google_model(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.start(state=ImgLlmGoogleSG.start,
                               data={'img': dialog_manager.start_data['img'], 'text': dialog_manager.start_data['text']})


async def select_sd3_model(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.next()
    await dialog_manager.start(state=ImgLlmSD3SG.start,
                               data={'img': dialog_manager.start_data['img'], 'text': dialog_manager.start_data['text']})

async def get_text(dialog_manager: DialogManager, i18n: TranslatorRunner, **kwargs):
    return {'change_request': i18n.change.request(),
            'your_request': i18n.your.request(),
            'send': i18n.send(),
            'search_to_replace': i18n.search.to.replace(),
            'search_prompt': i18n.search.prompt(),
            'replace_prompt': i18n.replace.prompt(),
            'remove_background': i18n.remove.background(),
            'upscale': i18n.upscale(),
            'create_video': i18n.create.video(),
            'need_time': i18n.need.time(),
            'text': dialog_manager.start_data['text']}

async def get_text_progress(dialog_manager: DialogManager, i18n: TranslatorRunner, **kwargs):
    return {'need_time': i18n.need.time(), 'progress': dialog_manager.dialog_data.get("progress", 0),}

async def get_new_request(dialog_manager: DialogManager, i18n: TranslatorRunner, **kwargs):
    return {'input_new_request': i18n.input.new.request()}

async def get_models(dialog_manager: DialogManager, i18n: TranslatorRunner, **kwargs):
    return {'google_img_analyze': i18n.google.img.analyze(),
            'sd3_img_analyze': i18n.sd3.img.analyze(),
            'select_model': i18n.select.model()}


async def get_request_google(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    try:
        await callback.bot.send_chat_action(callback.message.chat.id, action="typing")
        i18n: TranslatorRunner = dialog_manager.middleware_data.get('i18n')
        img_path = dialog_manager.start_data['img']
        response = response_google_model_for_image(img_path, dialog_manager.start_data['text'])
        await callback.message.answer(response)
    except Exception as ex:
        logging.error(ex)
        await callback.message.answer(i18n.error())
    finally:
        await dialog_manager.done(show_mode=ShowMode.NO_UPDATE)
        await dialog_manager.done(show_mode=ShowMode.NO_UPDATE)
        if os.path.exists(img_path):
            os.remove(img_path)


def check_text(text: str):
    return text


async def correct_text(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    dialog_manager.start_data['text'] = text
    await dialog_manager.back()


# Обрабатываем только нажатия кнопок пользователя в диалоге, никаких команд и запросов
async def no_func(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    pass


async def search_btn_click(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.next()


def check_search_prompt(text: str):
    return text

async def correct_search_prompt(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    dialog_manager.start_data['search_prompt'] = text
    await dialog_manager.next()

def check_replace_prompt(text: str):
    return text

async def correct_replace_prompt(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    try:
        await message.bot.send_chat_action(message.chat.id, action="typing")
        await dialog_manager.done()
        db: DB = dialog_manager.middleware_data.get('db')
        i18n: TranslatorRunner = dialog_manager.middleware_data.get('i18n')
        img_path = dialog_manager.start_data.get("img")
        dialog_manager.start_data['replace_prompt'] = text
        response = await response_search_replace_img_model(search_prompt=dialog_manager.start_data.get("search_prompt"),
                                                replace_prompt=dialog_manager.start_data.get("replace_prompt"),
                                                img=img_path,
                                                telegram_id=message.from_user.id,
                                                db=db,)

        if response == "no_key":
            await message.answer(i18n.keys.ended())
            await send_no_key(message.bot)
        else:
            if os.path.exists(f"{message.chat.id}.png"):
                await message.bot.send_chat_action(message.chat.id, action="upload_photo")
                img = FSInputFile(f"{message.chat.id}.png")
                if os.path.getsize(f"{message.chat.id}.png") < 10485760:
                    await message.answer_photo(img)
                await message.answer_document(img)
                os.remove(f"{message.chat.id}.png")
    except Exception as ex:
        logging.error(ex)
        await message.answer(i18n.error())
    finally:
        await dialog_manager.done(show_mode=ShowMode.NO_UPDATE)
        if os.path.exists(img_path):
            os.remove(img_path)


async def remove_back_click(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    try:
        await callback.bot.send_chat_action(callback.message.chat.id, action="typing")
        await dialog_manager.done()
        db: DB = dialog_manager.middleware_data.get('db')
        i18n: TranslatorRunner = dialog_manager.middleware_data.get('i18n')
        img_path = dialog_manager.start_data['img']
        response = await response_remove_background_img_model(img_path, callback.from_user.id, db)
        if response == "no_key":
            await callback.message.answer(i18n.keys.ended())
            await send_no_key(callback.message.bot)
        else:
            if os.path.exists(f"{callback.message.chat.id}.png"):
                await callback.bot.send_chat_action(callback.message.chat.id, action="upload_photo")
                img = FSInputFile(f"{callback.message.chat.id}.png")
                if os.path.getsize(f"{callback.message.chat.id}.png") < 10485760:
                    await callback.message.answer_photo(img)
                await callback.message.answer_document(img)
                os.remove(f"{callback.message.chat.id}.png")
    except Exception as ex:
        logging.error(ex)
        await callback.message.answer(i18n.error())
    finally:
        await dialog_manager.done(show_mode=ShowMode.NO_UPDATE)
        if os.path.exists(img_path):
            os.remove(img_path)

# Получить разрешение изображения
def check_dimension(img_path):
    with Image.open(img_path) as img:
        width, height = img.size
    return width, height


# Высокое качество изображения
async def upscale_click(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    try:
        flag = False
        await callback.bot.send_chat_action(callback.message.chat.id, action="typing")
        img_path = dialog_manager.start_data['img']
        db: DB = dialog_manager.middleware_data.get('db')
        i18n: TranslatorRunner = dialog_manager.middleware_data.get('i18n')
        # Проверка кол-ва пикселей изображения
        width, height = check_dimension(img_path)
        if width * height < 4096 or width * height > 1048576:
            await callback.message.answer(f"{i18n.size.image.need()} {width * height} {i18n.pixels()}")
        else:
            # Отправление запроса. В случае неудачи generation_id is None
            key, generation_id = await response_upscale_img_model(img_path, "upscale image to high definition and high quality", callback.from_user.id, db)
            if generation_id is None:
                await callback.message.answer(i18n.error())
                if key == "no_key":
                    await callback.message.answer(i18n.keys.ended())
                    await send_no_key(callback.message.bot)
        flag = True
    except Exception as ex:
        logging.error(ex)
        await callback.message.answer(i18n.error())
    finally:
        await dialog_manager.done()
        await dialog_manager.done()
        if os.path.exists(img_path):
            os.remove(img_path)

    # Получение результата
    if flag and 4096 <= width * height <= 1048576 and not generation_id is None:
        await dialog_manager.start(ProgressSG.processing)
        asyncio.create_task(response_upscale_img_result(callback, dialog_manager.bg(), callback.from_user.id, key, generation_id, i18n))


async def create_video_click(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    try:
        flag = False
        await callback.bot.send_chat_action(callback.message.chat.id, action="typing")
        db: DB = dialog_manager.middleware_data.get('db')
        i18n: TranslatorRunner = dialog_manager.middleware_data.get('i18n')
        img_path = dialog_manager.start_data['img']
        # Проверка разрешения изображения
        width, height = check_dimension(img_path)
        if not (width, height) in ((1024, 576), (576, 1024), (768, 768)):
            await callback.message.answer(f"{i18n.resolution.support()} 1024x576, 576x1024, 768x768.\n{i18n.your.image()} {width}x{height}")
        else:
            # Отправление запроса. В случае неудачи generation_id is None
            key, generation_id = await response_image_to_video_model(img_path, callback.from_user.id, db)
            if generation_id is None:
                await callback.message.answer(i18n.error())
                # Если неудачная попытка из-за отсутствия действующего ключа
                if key == "no_key":
                    await callback.message.answer(i18n.keys.ended())
                    await send_no_key(callback.message.bot)
        Flag = True
    except Exception as ex:
        logging.error(ex)
        await callback.message.answer(i18n.error())
    finally:
        await dialog_manager.done()
        await dialog_manager.done()
        if os.path.exists(img_path):
            os.remove(img_path)

    # Получение результата
    if Flag and (width, height) in ((1024, 576), (576, 1024), (768, 768)) and not generation_id is None:
        await dialog_manager.start(ProgressSG.processing)
        asyncio.create_task(response_image_to_video_result(callback, dialog_manager.bg(), callback.from_user.id, key, generation_id, i18n))


img_llm_select_dialog = Dialog(
    Window(
        Format('''{select_model}
              🅖 google-vision-pro {google_img_analyze}
              🌄 stable diffusion 3 {sd3_img_analyze}'''),
        Button(
            text=Const("🅖 google-vision-pro"),
            id="google_img_button",
            on_click=select_google_model),
        Button(
            text=Const("🌄 stable diffusion 3"),
            id="sd3_img_button",
            on_click=select_sd3_model),
        state=ImgLlmSelectSG.start,
        getter=get_models,
    ),
    Window(
        Format("🌄 stable diffusion 3"),
        Format("{need_time}"),
        MessageInput(
            func=no_func,
        ),
        state=ImgLlmSelectSG.processing,
        getter=get_text,
    ),
)


img_llm_dialog_google = Dialog(
    Window(
        Format("🅖 google-vision-pro\n{your_request}"),
        Format("{text}"),
        Row(
            Next(text=Format("{change_request}")),
            Button(
                text=Format("{send}"),
                id="run",
                on_click=get_request_google,
            ),),
        MessageInput(
            func=no_func,
        ),
        state=ImgLlmGoogleSG.start,
        getter=get_text,
    ),
    Window(
        Format("{input_new_request}"),
        TextInput(
            id='text_input',
            type_factory=check_text,
            on_success=correct_text,
        ),
        state=ImgLlmGoogleSG.text_input,
        getter=get_new_request,
    ),
)


img_llm_dialog_sd3 = Dialog(
    Window(
        Format("🌄 stable diffusion 3"),
        Column(
            Button(
                text=Format("🔍 {search_to_replace}"),
                id="search_btn",
                on_click=search_btn_click,
            ),
            Button(
                text=Format("✂ {remove_background}"),
                id="remove_back_btn",
                on_click=remove_back_click,
            ),
            Button(
                text=Format("🎇 {upscale}"),
                id='upscale_btn',
                on_click=upscale_click,
            ),
            Button(
                text=Format("🎥 {create_video}"),
                id='create_video_btn',
                on_click=create_video_click,
            ),
        ),
        state=ImgLlmSD3SG.start,
        getter=get_text,
    ),
    Window(
        Format("{search_prompt}"),
        TextInput(
            id='search_prompt_input',
            type_factory=check_search_prompt,
            on_success=correct_search_prompt,
        ),
        MessageInput(
            func=no_func,
        ),
        state=ImgLlmSD3SG.search_prompt_input,
        getter=get_text,
    ),
    Window(
        Format("{replace_prompt}"),
        TextInput(
            id='replace_prompt_input',
            type_factory=check_replace_prompt,
            on_success=correct_replace_prompt,
        ),
        MessageInput(
            func=no_func,
        ),
        state=ImgLlmSD3SG.replace_prompt_input,
        getter=get_text,
    ),
)

progress_bar = Dialog(
    Window(
        Multi(
            Const("🌄 stable diffusion 3"),
            Format("{need_time}"),
            Progress("progress", 10, filled='🟩'),
            ),
        state=ProgressSG.processing,
        getter=get_text_progress,
    ),
)