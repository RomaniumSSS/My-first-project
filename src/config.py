from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    BOT_TOKEN: SecretStr
    OPENAI_KEY: SecretStr
    OPENAI_MODEL: str = "gpt-4o"  # Default to gpt-4o, support gpt-5.1 if available

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


config = Settings()
