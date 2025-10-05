# tests/test_filters.py
from datetime import datetime, timezone
from app import create_app

def test_localdt_formats_naive_and_aware():
    app = create_app(testing=True)
    with app.app_context():
        f = app.jinja_env.filters["localdt"]
        # naive (treated as UTC)
        out1 = f(datetime(2025, 1, 2, 3, 4, 5))
        assert isinstance(out1, str) and len(out1) >= 10
        # aware UTC
        out2 = f(datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc))
        assert isinstance(out2, str) and len(out2) >= 10
        # None -> empty string
        assert f(None) == ""