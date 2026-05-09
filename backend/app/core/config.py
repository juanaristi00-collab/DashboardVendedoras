from pathlib import Path
from pydantic_settings import BaseSettings

# El .env vive en Dashboard CRM/ (un nivel arriba de backend/)
_ENV_FILE = Path(__file__).parent.parent.parent.parent / ".env"


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int = 3309          # Puerto real del servidor Zoftkrates
    DB_NAME_SAANYE: str          # Nombre exacto del .env
    DB_USER: str
    DB_PASSWORD: str             # Nombre exacto del .env

    model_config = {
        "env_file": str(_ENV_FILE) if _ENV_FILE.exists() else None,
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }


settings = Settings()
