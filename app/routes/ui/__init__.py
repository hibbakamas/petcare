"""
UI (server-rendered) blueprint registry.

Exports all UI blueprints so the app factory can register them in one place.
"""

from .auth_ui import auth_ui
from .entries_ui import entries_ui
from .home_ui import home_ui
from .households_ui import households_ui
from .pets_ui import pets_ui
from .users_ui import users_ui
from .health_ui import bp as health_ui_bp

# Central list used by app.app:create_app() to register UI routes.
ui_blueprints = [auth_ui, households_ui, pets_ui, users_ui, home_ui, entries_ui, health_ui_bp]

__all__ = ["ui_blueprints"]
