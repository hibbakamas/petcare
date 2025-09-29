# loads environment variables

import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # path to /app
INSTANCE_DIR = os.path.join(BASE_DIR, '..', 'instance')
os.makedirs(INSTANCE_DIR, exist_ok=True)  # make sure instance/ exists

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        f"sqlite:///{os.path.join(INSTANCE_DIR, 'petcare.db')}"
    )