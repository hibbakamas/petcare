# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))          # .../app
INSTANCE_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "instance"))
os.makedirs(INSTANCE_DIR, exist_ok=True)  # ensure instance/ exists

def _sqlite_path(filename: str) -> str:
    # absolute path so CWD never matters
    return "sqlite:///" + os.path.join(INSTANCE_DIR, filename)

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", _sqlite_path("petcare.db"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestingConfig(Config):
    TESTING = True
    # in-memory DB for tests only
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"