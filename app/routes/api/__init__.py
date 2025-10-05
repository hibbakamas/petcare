from .auth import auth_bp
from .households import households_bp
from .pets import pets_bp
from .entries import entries_bp

api_blueprints = [auth_bp, households_bp, pets_bp, entries_bp]
