from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.text import Format
from aiogram_dialog.widgets.kbd import Select, Column
from aiogram_dialog import Dialog, Window, DialogManager
from fluentogram import TranslatorRunner

from states import LlmSG
from asyncpg import Record
from database.database import DB


async def get_llms(dialog_manager: DialogManager, i18n: TranslatorRunner, db: DB, **kwargs):
    llms: Record = await db.get_llms()
    return {'select_llm': i18n.select.llm(), 'llms': llms}

async def set_llm(callback: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    try:
        db: DB = dialog_manager.middleware_data.get('db')
        i18n: TranslatorRunner = dialog_manager.middleware_data.get('i18n')
        llm: Record = await db.set_llm_to_user(telegram_id=callback.message.chat.id, telegram_username=callback.from_user.username,
                                telegram_name=callback.from_user.first_name, llm_id=int(item_id))
        if callback.message.chat.type == "private":
            msg = await callback.message.answer(f'{llm[0].get("img")} {llm[0].get("name")}\n{i18n.send.request()}')
        else:
            await callback.message.answer(f'{llm[0].get("img")} {llm[0].get("name")}')
        await callback.message.bot.delete_message(callback.message.chat.id, callback.message.message_id)
    except:
        await callback.message.answer(i18n.error())
    finally:
        await dialog_manager.done()



llm_dialog = Dialog(
    Window(
        Format('{select_llm}'),
        Column(
            Select(
                Format('{item[2]} {item[1]}'),
                id='llm',
                item_id_getter=lambda x: x[0],
                items='llms',
                on_click=set_llm,
            )),
        state=LlmSG.start,
        getter=get_llms
    )
)