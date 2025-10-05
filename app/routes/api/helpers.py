from flask import jsonify

def json_error(msg: str, status: int):
    """Return a minimal, consistent JSON error body."""
    return jsonify(error=msg), status