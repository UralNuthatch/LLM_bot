from aiogram.types import Message
from services.models.google import response_google_model
from services.models.gpt4free import response_gpt4free_model_text, response_gpt4free_model_img
from services.models.idb_openai import response_idb_openai_model
from services.models.stability import response_stability_img_model
from database.database import DB


async def select_model_category(llm_category: int, llm_model, text_request: str, telegram_id: int, db: DB=None) -> str:
    match llm_category:
        case 1:
            return response_google_model(llm_model, text_request)
        case 2:
            return response_gpt4free_model_text(llm_model, text_request)
        case 3:
            return response_idb_openai_model(llm_model, text_request)
        case 4:
            return await response_stability_img_model(text_request, telegram_id, db)
        case 5:
            return await response_gpt4free_model_img(llm_model, text_request, telegram_id)
