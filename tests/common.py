"""Test helpers for discovering API routes, filling URL params, and extracting ids."""

import re
from typing import Iterable, Optional


def find_api_route(app, contains: Iterable[str], method: str) -> Optional[str]:
    """Return the first /api route whose rule contains all substrings and supports method."""
    method = method.upper()
    for rule in app.url_map.iter_rules():
        path = str(rule.rule)
        if not path.startswith("/api"):
            continue
        if not rule.methods or method not in rule.methods:
            continue
        if all(s in path for s in contains):
            return path
    return None


_param_re = re.compile(r"<(?:[^:>]+:)?(?P<name>[^>]+)>")


def fill_route_params(rule: str, **params) -> str:
    """Replace <...> params in a rule with provided **params; raises KeyError on missing."""
    def repl(m):
        name = m.group("name")
        if name not in params:
            raise KeyError(f"Missing URL param: {name} for rule {rule}")
        return str(params[name])
    return _param_re.sub(repl, rule)


def extract_int(d, keys=("id", "household_id", "pet_id", "entry_id")) -> Optional[int]:
    """Find an integer id in a JSON-like dict using common keys; recurses into nested dicts."""
    if not isinstance(d, dict):
        return None
    for k in keys:
        v = d.get(k)
        if isinstance(v, int):
            return v
        if isinstance(v, dict):
            inner = extract_int(v, keys)
            if inner is not None:
                return inner
    for v in d.values():
        if isinstance(v, int):
            return v
        if isinstance(v, dict):
            inner = extract_int(v, keys)
            if inner is not None:
                return inner
    return None