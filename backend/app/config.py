import json
import os


class Config:
    DEBUG: bool = eval(os.environ.get("DEBUG", False))
    APP = os.environ.get("FLASK_APP")
    PORT: int = int(os.environ.get("PORT", 5000))
    SECRET_KEY = os.environ.get("SECRET_KEY", "secret")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "secret")
    JWT_ACCESS_EXPIRES: int = int(os.environ.get("JWT_ACCESS_EXPIRES", 10))
    JWT_REFRESH_EXPIRES: int = int(os.environ.get("JWT_REFRESH_EXPIRES", 10))
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "max_overflow": 10,
        "pool_recycle": 30,
        "pool_pre_ping": True,
    }
