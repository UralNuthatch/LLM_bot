import requests
from g4f.client import Client
from g4f.cookies import set_cookies



def response_gpt4free_model_text(llm_model, text_request: str) -> str:
    client = Client()
    response = client.chat.completions.create(
        model=llm_model,
        messages=[{"role": "user", "content": text_request}],
    )
    return response.choices[0].message.content


async def response_gpt4free_model_img(model, prompt: str, telegram_id: int) -> str:
    set_cookies(".bing.com", {
    "_U": "1xmR0nNDVpm_nPAZF2r9LljYQ7GX55IBsurpvmwDK9FYrAMZ4m2ZlEZmyeGYCoM9w4PDN4VSMMv485GlTcFno3V_tcE27QhVuGZVY_Y3YS4_9npOIMBVkGk2xMz3Id_T5qcHn2YBG3wK-ZJyU-G_SehI8tGIU_dPizKK-RUTTjQVPBTam_3mOF2PWvZf_-F4JhHdTf4N7bzes5dSCfTcXFw"})

    set_cookies(".google.com", {
  "__Secure-1PSID": "g.a000iwizmeheF9bs_EdCkFRgUBLO2Ljh0gy8bOOqZ8tFpo_75o9TKwn7mfMVjRYmNa7AMfeKtAACgYKAcASAQASFQHGX2Mi60H86QQThqe0csByXH9o_xoVAUF8yKrA1G_RAhhsDScxFf_t7mQk0076"
    })
    client = Client()
    response = client.images.generate(
        model=model,
        prompt=prompt,
    )
    image_url = response.data[0].url

    # Скачиваем файл на локальную машину
    response = requests.get(image_url)
    with open(f"{telegram_id}.png", "wb") as file:
        file.write(response.content)

    return 'image'