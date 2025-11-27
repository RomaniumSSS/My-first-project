from typing import List, Union

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: SecretStr
    OPENAI_KEY: SecretStr
    OPENAI_MODEL: str = "gpt-4o"  # Default to gpt-4o, support gpt-5.1 if available
    
    # Alpha Testing: Whitelist
    # Support List[int] directly or comma-separated string "123,456"
    ALLOWED_USER_IDS: List[int] = []

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("ALLOWED_USER_IDS", mode="before")
    @classmethod
    def parse_allowed_ids(cls, v: Union[str, List[Any]]) -> List[int]:
        if isinstance(v, str):
            if not v.strip():
                return []
            # Handle "[1, 2]" JSON style or "1, 2" CSV style
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass  # Fallback to CSV
            
            return [int(x.strip()) for x in v.split(",") if x.strip().isdigit()]
        return v


config = Settings()
