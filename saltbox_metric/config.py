import logging.config
import os
from datetime import timedelta
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_NAME = 'Salt.Box Metric'
APP_DESC = 'Salt.Box Metric API'
CACHE_LIFETIME = timedelta(days=1)
ENV_FILE = Path(os.environ.get('SALTBOX_METRIC_ENV_FILE', '.env'))


class Settings(BaseSettings):
    base_url_root_path: str = '/'
    debug: bool = False
    origins: list[str] = Field(['*'], description='CORS allowed resources')

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra='ignore')


SETTINGS = Settings()


class LogConfig(BaseModel):
    LOG_FORMAT: str = '%(levelprefix)s [%(filename)s:%(lineno)d] %(message)s'
    LOG_LEVEL: str = 'DEBUG'  # if SETTINGS.debug else 'INFO'

    version: int = 1
    disable_existing_loggers: bool = False
    formatters: dict = {
        'default': {
            '()': 'uvicorn.logging.DefaultFormatter',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'fmt': LOG_FORMAT,
        },
    }
    handlers: dict = {
        'default': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': 'ext://sys.stderr',
        },
    }
    loggers: dict = {
        'saltbox_metric': {
            'handlers': ['default'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
    }


LOG_CONFIG = LogConfig()

logging.config.dictConfig(LOG_CONFIG.model_dump())

logger = logging.getLogger('saltbox_metric')
