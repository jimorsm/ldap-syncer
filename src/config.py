import logging
import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional, Union

from pydantic import BaseSettings

LOG_LEVEL = [
    "CRITICAL",
    "FATAL",
    "ERROR",
    "WARN",
    "WARNING",
    "INFO",
    "DEBUG",
    "NOTSET",
]


class Settings(BaseSettings):
    LDAP_SERVER: str
    LDAP_PORT: int = 389
    LDAP_ADMIN: str
    LDAP_ADMIN_PASSWD: str
    ROOT_DN: str = "dc=example,dc=org"
    DINGDING_APPKEY: str = "dingxcjnj8ek623nlx1a"
    DINGDING_APPSECRET: str = (
        "yPJQBOZ3s93qsR9OOmuq3wpkyeBWfUYsq4uK-BOQrjHWc0Ik2nszkfs1P8u1P3KR"
    )
    LOG_LEVEL: str = "info"

    class Config:
        env_file = ".env"


class Testing(Settings):
    LOG_LEVEL: str = "debug"

    class Config:
        env_file = ".testing.env"


class Production(Settings):
    pass


# @lru_cache
def get_settings():
    env = os.getenv("ENV", "TESTING")
    if env == "PRODUCTION":
        setting = Production()
    else:
        setting = Testing()
    logging.basicConfig(level=setting.LOG_LEVEL.upper())
    return setting


setting = get_settings()
