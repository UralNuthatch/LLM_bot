from aiogram.types import Message
from services.models.google import response_google_model
from services.models.gpt4free import response_gpt4free_model_text, response_gpt4free_model_img
from services.models.idb_openai import response_idb_openai_model
from services.models.stability import response_stability_img_model
from services.models.fireworks import response_fireworks
from services.models.openai import response_openai
from database.database import DB


async def select_model_category(llm_category: int, llm_model, text_request: str, telegram_id: int, db: DB=None, messages=None) -> str:
    match llm_category:
        case 1:
            return response_google_model(llm_model, text_request, messages)
        case 2:
            return response_gpt4free_model_text(llm_model, messages)
        case 3:
            return response_idb_openai_model(llm_model, messages)
        case 4:
            return await response_stability_img_model(text_request, telegram_id, db)
        case 5:
            return response_gpt4free_model_img(llm_model, text_request, telegram_id)
        case 6:
            return response_fireworks(llm_model, messages)
        case 7:
            return response_openai(llm_model, messages)
