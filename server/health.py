from __future__ import annotations
import sqlite3
from pathlib import Path

def estado(db_path: Path, consultar_fn=None) -> dict:
    try:
        if not db_path.exists():
            return {'estado': 'degraded', 'db': 'missing'}
        with sqlite3.connect(str(db_path), timeout=2) as conn:
            conn.execute('SELECT 1')
        return {'estado': 'healthy', 'db': 'ok'}
    except Exception:
        return {'estado': 'degraded', 'db': 'error'}
