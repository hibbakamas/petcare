# makes "app" a Python package

# app/__init__.py
from .app import create_app, app  # re-export factory and the module-level app

__all__ = ["create_app", "app"]