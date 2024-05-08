import google.generativeai as genai
from PIL import Image
from config_data.config import load_config, Config


def response_google_model(llm_model, text_request: str, messages: list):
        config: Config = load_config()
        genai.configure(api_key=config.api_key)
        model = genai.GenerativeModel(llm_model)

        google_messages = []
        for m in messages:
                google_messages.append({
                        "role": m["role"] if m["role"] == "user" else "model",    # Меняем assistant на model для роли модели
                        "parts": [m["content"]]
                })
        
        response = model.generate_content(google_messages)
        return response.text


def response_google_model_for_image(img_path, text:str):
        model = genai.GenerativeModel("gemini-pro-vision")
        with Image.open(img_path) as img:
                response = model.generate_content([text, img], stream=True)
                response.resolve()
        return response.text