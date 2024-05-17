from openai import OpenAI
from config_data.config import load_config, Config


def response_openai(llm_model, messages: list) -> str:
    config: Config = load_config()
    client = OpenAI(api_key=config.api_key_openai)
    response = client.chat.completions.create(
                                            model=llm_model,
                                            messages=messages,
                                            )
    return response.choices[0].message.content