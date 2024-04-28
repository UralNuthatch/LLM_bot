from environs import Env
from dataclasses import dataclass


@dataclass
class TgBot:
    token: str      # токен телеграм-бота

@dataclass
class DatabaseConfig:
    database: str
    db_host: str
    db_user: str
    db_password: str

@dataclass
class Config:
    tgbot: TgBot
    api_key: str    # API ключ Gemini (можно получить на https://makersuite.google.com/app/apikey)
    api_key_idb: str # API_KEY https://idb.ai
    idb_base: str
    db: DatabaseConfig


def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)

    return Config(tgbot=TgBot(token=env("BOT_TOKEN")),
                  api_key=env("API_KEY"), api_key_idb=env("API_KEY_IDB"), idb_base=env("IDB_BASE"),
                  db=DatabaseConfig(database=env("DATABASE"), db_host=env("DB_HOST"),
                                    db_user=env("DB_USER"), db_password=env("DB_PASSWORD")))
