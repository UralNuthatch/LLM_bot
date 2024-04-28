import google.generativeai as genai
from PIL import Image
from config_data.config import load_config, Config


def response_google_model(llm_model, text_request: str):
        config: Config = load_config()
        genai.configure(api_key=config.api_key)
        model = genai.GenerativeModel(llm_model)
        response = model.generate_content(text_request)
        # Удаляем символы, которые ломают MARKDOWN и вызывают Telegram bad request
        text = response.text.replace("* ", "")
        return response.text


def response_google_model_for_image(img_path, text:str):
        model = genai.GenerativeModel("gemini-pro-vision")
        with Image.open(img_path) as img:
                response = model.generate_content([text, img], stream=True)
                response.resolve()
        return response.text