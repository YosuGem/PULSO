"""Ingesta de muestra EN para rollout multilingüe (Bloque 4 - T13)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from noosfera_project.servicios.persistencia import crear_base

DB = Path(__file__).resolve().parents[1] / "eventos.db"

MUESTRA_EN = [
    ("reddit_worldnews", "Bitcoin price prediction 2026: experts say 120k is the new floor after ETF approval"),
    ("reddit_worldnews", "Ukraine war latest: Russian offensive near Kharkiv intensifies as ceasefire talks stall"),
    ("hackernews", "US elections 2026: senate races tighten as congress debates voting reform"),
    ("hackernews", "Inflation in Europe hits 3.2% as ECB holds rates steady amid energy price shocks"),
    ("reddit_wallstreet", "S&P 500 closes at record high as Nasdaq rallies on AI earnings beat"),
    ("reddit_soccer", "Spain national team qualifies for World Cup 2026 after dominant win in qualifier"),
    ("reddit_crypto", "Ethereum upgrade reduces gas fees, boosting DeFi activity across chains"),
    ("hackernews", "Putin signals willingness to negotiate as Ukraine conflict enters third year"),
    ("reddit_worldnews", "Trump leads polls for 2026 US presidential election amid congressional gridlock"),
    ("hackernews", "European Central Bank warns of persistent inflation as eurozone growth slows"),
    ("reddit_wallstreet", "Dow Jones and Nasdaq both up as Wall Street bets on soft landing scenario"),
    ("reddit_soccer", "La Roja prepares for World Cup with new lineup under revised coaching staff"),
]

import logging

def ingerir():
    crear_base()
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")
    # Migración: añadir columna idioma si no existe (B2)
    cur = conn.execute("PRAGMA table_info(lenguaje_colectivo)")
    cols = [r[1] for r in cur.fetchall()]
    if "idioma" not in cols:
        conn.execute("ALTER TABLE lenguaje_colectivo ADD COLUMN idioma TEXT DEFAULT 'es'")
    import hashlib
    count = 0
    for fuente, texto in MUESTRA_EN:
        h = hashlib.sha1(texto.encode("utf-8", errors="ignore")).hexdigest()[:12]
        try:
            conn.execute(
                "INSERT INTO lenguaje_colectivo (fuente, texto, texto_hash, publicado, creado_en, idioma) VALUES (?,?,?,?,?,?)",
                (fuente, texto, h, None, "2026-07-16T00:00:00", "en"),
            )
            count += 1
        except sqlite3.IntegrityError as exc:
            logging.warning("documento duplicado o conflicto, se omite: %s", exc)
            pass
    conn.commit()
    conn.close()
    print(f"Ingeridos {count} docs EN")


if __name__ == "__main__":
    ingerir()
