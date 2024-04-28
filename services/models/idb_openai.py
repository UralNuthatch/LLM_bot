from openai import OpenAI
from config_data.config import load_config, Config


def response_idb_openai_model(llm_model, text_request):
    config: Config = load_config()
    client = OpenAI(
        api_key=config.api_key_idb,
        base_url=config.idb_base
    )

    completion = client.chat.completions.create(
    model=llm_model,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": text_request}
    ],
    stream=False
    )

    return completion.choices[0].message.content