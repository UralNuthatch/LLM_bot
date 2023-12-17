from environs import Env
from dataclasses import dataclass


@dataclass
class TgBot:
    token: str      # токен телеграм-бота

@dataclass
class Config:
    tgbot: TgBot
    api_key: str    # API ключ Gemini (можно получить на https://makersuite.google.com/app/apikey)


def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)

    return Config(tgbot=TgBot(token=env("BOT_TOKEN")),
                  api_key=env("API_KEY"))
