"""Ingesta de muestra DE para rollout multilingüe (Bloque A)."""
from __future__ import annotations

import sqlite3
import hashlib
from pathlib import Path

from noosfera_project.servicios.persistencia import crear_base

DB = Path(__file__).resolve().parents[1] / "eventos.db"

import logging
MUESTRA_DE = [
    ("reddit_de", "Der Bitcoin Preis soll 2026 auf 120.000 Dollar steigen laut Experten"),
    ("spiegel", "Krieg in der Ukraine: Russische Offensive bei Charkiw verstarkt sich"),
    ("zeit", "US-Wahlen 2026: Der Senat polarisiert vor der Abstimmung"),
    ("tagesschau", "Inflation in Europa: EZB halt Zinsen trotz Preisanstieg"),
    ("reddit_de", "Der DAX erreicht Rekord wahrend Wall Street bei KI-Ergebnissen rallyt"),
    ("kicker", "Deutsche Nationalmannschaft fur Weltmeisterschaft 2026 qualifiziert nach Sieg"),
    ("reddit_crypto_de", "Ethereum: Update senkt Gas-Gebuhren und boostet DeFi"),
    ("spiegel", "Putin offnet Tur fur Verhandlung wahrend Konflikt in drittes Jahr geht"),
    ("zeit", "Trump fuhrt in Umfragen 2026 wahrend Kongress blockiert ist"),
    ("tagesschau", "Europaische Zentralbank warnt vor anhaltender Inflation in Eurozone"),
    ("reddit_de", "Dow Jones und Nasdaq steigen nach Erwartungen fur weiche Landung"),
    ("kicker", "Die Mannschaft bereitet WM mit neuem Kader vor"),
]


def ingerir():
    crear_base()
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.execute("PRAGMA table_info(lenguaje_colectivo)")
    cols = [r[1] for r in cur.fetchall()]
    if "idioma" not in cols:
        conn.execute("ALTER TABLE lenguaje_colectivo ADD COLUMN idioma TEXT DEFAULT 'es'")
    count = 0
    for fuente, texto in MUESTRA_DE:
        h = hashlib.sha1(texto.encode("utf-8", errors="ignore")).hexdigest()[:12]
        try:
            conn.execute(
                "INSERT INTO lenguaje_colectivo (fuente, texto, texto_hash, publicado, creado_en, idioma) VALUES (?,?,?,?,?,?)",
                (fuente, texto, h, None, "2026-07-16T00:00:00", "de"),
            )
            count += 1
        except sqlite3.IntegrityError as exc:
            logging.warning("documento duplicado o conflicto, se omite: %s", exc)
            pass
    conn.commit()
    conn.close()
    print(f"Ingeridos {count} docs DE")


if __name__ == "__main__":
    ingerir()
