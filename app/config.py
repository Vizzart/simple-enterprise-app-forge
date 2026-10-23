import os

from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    """

    """

    APP_NAME = os.getenv('APP_NAME', 'SEAF')

    FLASK_RUN_PORT = os.getenv('FLASK_RUN_PORT')

    MAX_CONTENT_LENGTH = os.getenv('MAX_CONTENT_LENGTH')

    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'max_overflow': 10,
        'pool_recycle': 120,
        'pool_pre_ping': True
    }

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    SECRET_KEY = os.getenv('SECRET_KEY')

    FLASK_DEBUG = True

    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_PERMANENT = True

    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_SQLALCHEMY_DATABASE_URL')


config = {
    'dev': DevelopmentConfig,
    'default': DevelopmentConfig
}


