# main entrypoint, creates flask app

from flask import Flask
from .config import Config
from .db import db, migrate

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)