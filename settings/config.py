from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    DEV: bool = False

    BOT_TOKEN: SecretStr = ''

    PAGE_SCROLLING_SPEED: float = 0.3
    MAX_N_PAGES_TO_SEARCH_IN_CATALOG: int = 30

    class Config:
        env_file = Path(BASE_DIR, 'settings', 'env')


settings = Settings()
