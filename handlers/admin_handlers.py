import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.text import List, Format
from aiogram_dialog.widgets.kbd import Button, Cancel, Next
from aiogram_dialog.widgets.input import TextInput, ManagedTextInput
from fluentogram import TranslatorRunner

from database.database import DB
from states import ViewKeysSG
from services.models.stability import balance


logger = logging.getLogger(__name__)


router = Router()


@router.message(Command(commands="keys"))
async def view_and_add_keys(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=ViewKeysSG.start, mode=StartMode.RESET_STACK)


async def get_keys(dialog_manager: DialogManager, db: DB, i18n: TranslatorRunner, **kwargs):
    # Показываем из базы все ключи с кредитами больше чем 1.5; 2 = минимальная стоимость генерации изборажения
    keys = await db.all_keys(1.5)
    return {"keys": keys, 'add_key': i18n.add.key(), 'cancel': i18n.cancel(),
            'instruction_add_key': i18n.instruction.add.key(), 'available_keys': i18n.available.keys()}


def key_check(text: str) -> str:
    if text == "/cancel":
        return text
    # Проверка формата ключа
    if text.startswith("sk-") and len(text) == 51:
        try:
            credits = balance(text)
            if int(credits) > 0:
                return text
        except Exception as ex:
            logging.error(ex)
            raise ValueError
    raise ValueError



async def correct_key_handler(message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str):
    if text != '/cancel':
        i18n: TranslatorRunner = dialog_manager.middleware_data.get('i18n')
        db: DB = dialog_manager.middleware_data.get('db')
        await db.add_key(text)
        await message.answer(i18n.added.key())
    await dialog_manager.back()


async def error_key_handler(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        error: ValueError):
    i18n: TranslatorRunner = dialog_manager.middleware_data.get('i18n')
    await message.answer(text=f"{i18n.error.input.key()}\n{i18n.command.cancel()}")


async def enter_key(dialog_manager: DialogManager, i18n: TranslatorRunner, **kwargs):
    return {'enter_key': i18n.enter.key()}


keys_dialog = Dialog(
    Window(
        Format("*{available_keys}:*"),
        List(field=Format('*{item[1]}... = {item[2]} credits*'),
            items='keys'),
        Format("\n{instruction_add_key}"),
        Next(
            text=Format("{add_key}"),
            id='add_key_btn',
        ),
        Cancel(
            text=Format("{cancel}")
        ),
        getter=get_keys,
        state=ViewKeysSG.start,
    ),
    Window(
        Format(text="{enter_key}"),
        TextInput(
            id='key_input',
            type_factory=key_check,
            on_success=correct_key_handler,
            on_error=error_key_handler,
        ),
        getter=enter_key,
        state=ViewKeysSG.input_key
    )
)