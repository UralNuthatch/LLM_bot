from openai import OpenAI
from config_data.config import load_config, Config


def response_idb_openai_model(llm_model, messages):
    config: Config = load_config()
    client = OpenAI(
        api_key=config.api_key_idb,
        base_url=config.idb_base
    )

    messages = [
      {
        "role": "system",
        "content": "You are a helpful assistant."
      } ] + messages
    
    completion = client.chat.completions.create(
                                                model=llm_model,
                                                messages=messages,
                                                stream=False)

    return completion.choices[0].message.content