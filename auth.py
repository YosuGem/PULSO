import os
import re
from http.server import BaseHTTPRequestHandler

_BEARER_RE = re.compile(r'(?i)^\s*Bearer\s+(.+)\s*$')
_ENV_KEY = 'NOOSFERA_API_KEY'

def _configured_keys() -> list[str]:
    raw = os.environ.get(_ENV_KEY, '')
    if not raw:
        return []
    return [k.strip() for k in raw.split(',') if k.strip()]

def authorized(auth_header: str | None) -> bool:
    if not _configured_keys():
        raise RuntimeError('NOOSFERA_API_KEY no configurada; auth obligatoria.')
    if not auth_header:
        return False
    m = _BEARER_RE.match(auth_header)
    if not m:
        return False
    return m.group(1) in set(_configured_keys())
