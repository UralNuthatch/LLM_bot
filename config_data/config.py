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
class RedisConfig:
    redis_host: str
    redis_port: int
    redis_db: int

@dataclass
class Config:
    tgbot: TgBot
    api_key: str    # API ключ Gemini (можно получить на https://makersuite.google.com/app/apikey)
    api_key_idb: str # API_KEY https://idb.ai
    api_key_fireworks: str # https://fireworks.ai/api-keys
    idb_base: str
    db: DatabaseConfig
    redis: RedisConfig


def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)

    return Config(tgbot=TgBot(token=env("BOT_TOKEN")),
                  api_key=env("API_KEY"), api_key_idb=env("API_KEY_IDB"),
                  api_key_fireworks=env("API_KEY_FIREWORKS"), idb_base=env("IDB_BASE"),
                  db=DatabaseConfig(database=env("DATABASE"), db_host=env("DB_HOST"),
                                    db_user=env("DB_USER"), db_password=env("DB_PASSWORD")),
                    redis=RedisConfig(redis_host=env("REDIS_HOST"), redis_port=env("REDIS_PORT"), redis_db=env("REDIS_DB")))
