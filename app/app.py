# main entrypoint

from flask import Flask
from .config import Config
from .db import db, migrate
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

# enable foreign keys for sqlite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON;")
        cur.close()

# create app and configure database
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)