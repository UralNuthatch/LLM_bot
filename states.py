from aiogram.fsm.state import StatesGroup, State


class LlmSG(StatesGroup):
    start = State()


class ViewKeysSG(StatesGroup):
    start = State()
    input_key = State()


class ImgLlmGoogleSG(StatesGroup):
    start = State()
    text_input = State()


class ImgLlmSD3SG(StatesGroup):
    start = State()
    search_prompt_input = State()
    replace_prompt_input = State()


class ImgLlmSelectSG(StatesGroup):
    start = State()
    processing = State()


class ProgressSG(StatesGroup):
    processing = State()