import openai
from config_data.config import Config, load_config


def response_fireworks(llm_model, messages: list):
    config: Config = load_config()
    client = openai.OpenAI(
        base_url = "https://api.fireworks.ai/inference/v1",
        api_key=config.api_key_fireworks,
    )
    response = client.chat.completions.create(
                                                model=f"accounts/fireworks/models/{llm_model}",
                                                messages=messages,
                                            )
    return response.choices[0].message.content