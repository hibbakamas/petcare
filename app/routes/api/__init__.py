"""
JSON API package.

Exports all API blueprints so the app factory can register them in one place.
"""

from .auth import auth_bp
from .entries import entries_bp
from .households import households_bp
from .pets import pets_bp
from .health import bp as health_bp

# Central list used by app.app:create_app() to register the API routes.
api_blueprints = [auth_bp, households_bp, pets_bp, entries_bp, health_bp]

__all__ = ["api_blueprints"]