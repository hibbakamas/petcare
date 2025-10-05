"""Flask application package.

Expose the factory and the module-level app for WSGI/CLI use.
"""

from .app import app, create_app

__all__ = ["create_app", "app"]
