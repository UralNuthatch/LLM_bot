import requests
import logging
import g4f
from g4f.client import Client
from g4f.cookies import set_cookies


logger = logging.getLogger(__name__)


def response_gpt4free_model_text(llm_model, messages: list) -> str:
    client = Client()

    response = client.chat.completions.create(
        model=llm_model,
        messages=messages,
    )

    return response.choices[0].message.content


def response_gpt4free_model_img(model, prompt: str, telegram_id: int) -> str:
    set_cookies(".bing.com", {
    "_U": "1lS3CvJhBbpB1eB3m18u4EJJMwkkPpTIXeBFGNSZjlRXpklTcJq4HMFiZwXhhmWNapR_cjqsKcvuVdEqz7UwEqMg3ieaDmYC8CPo18P0S3Hfv_Ezc_cXGZsLm5N4Jm1JwptwlXYNtnKDKJFojZ3OymNkonNYEfbgPgw4pqUv6ct7xM3_Y6LC4Y1XzpURCteJOoM0o-v4RyQKOkc2OzuFh-OaLo3mZ4jMOH3GRzuHB7fg"})

    set_cookies(".google.com", {
  "__Secure-1PSID": "g.a000jAjvMQJostwaKWWLfZADL5B3EnAFCzdjrUe2bRmueUL8XzZHHahJ-7mH-OFc4VnBKbF2WwACgYKAcESAQASFQHGX2MiPoT9hJqEiL_9ioaD7Ao59BoVAUF8yKo67p0SwTmJBVT7LXO9SjUJ0076"
    })
    try:
        client = Client()
        response = client.images.generate(
            model=model,
            prompt=prompt,
        )
    except:
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

    imgages_count = 4
    if model == "gemini-pro":
        imgages_count = 1

    # Скачиваем файлы на локальную машину
    for i in range(imgages_count):
        image_url = response.data[i].url
        img_data = requests.get(image_url)
        with open(f"{telegram_id}_{i}.png", "wb") as file:
            file.write(img_data.content)


# _U:"1GKwFA2dVQaxvQUBoDC6yDtFzWFIe1pDSkenz_nxwnT_o0SEbryDClwOiRYOGaJdcT5Am3SbuIn9VyX5nUPpZ61pEzO3hLhcJYKaRyCEnqQ12YmX3AoLJfTNBaTsKgdOW53eyvju1zt3Qou25dXoyCMk46RLJBcYkHO_vm1USto4wbDAkzcBHIdqzMzZha0BKewapSbYsUc7puM6vO2QLMADzMwmRj317FmQZK0XzJ9o"

# __Secure-1PSID:"g.a000jAhw1steAVvjQBk7Vma13R6KxSa4Yox76VbFFkhqakEZ8vdasgaMMxXxW38uCOA0wAolSAACgYKAdMSAQASFQHGX2MinIHPGwTTevbaeFR_2LQ3khoVAUF8yKqMjPRy-Xi4iXmbH6jq5VQy0076"


# _U:"1YbGJa7X25mTTMqAKJtN7Z1YUiPRQW6QzebAqx4gXh5_VmGwnykcAr0JZHsXYMPgk5x1js-s6EP3oThtxb20dbCjazpSHYw0oOEJZa25OcxfbLqBE-i1Y3inbZwMsf0HVnbo6M8zealJkuktaur4U7mReYO3OK0Ov41vHjuNqggMXZhpK83gAXtbxFz-Fiq_EBIx3fZarGEM_jazEcDDTNg"


# __Secure-1PSID:"g.a000jAjvMQJostwaKWWLfZADL5B3EnAFCzdjrUe2bRmueUL8XzZHHahJ-7mH-OFc4VnBKbF2WwACgYKAcESAQASFQHGX2MiPoT9hJqEiL_9ioaD7Ao59BoVAUF8yKo67p0SwTmJBVT7LXO9SjUJ0076"