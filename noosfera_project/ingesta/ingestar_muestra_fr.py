"""Ingesta de muestra FR para rollout multilingüe (Bloque A)."""
from __future__ import annotations

import sqlite3
import hashlib
from pathlib import Path

from noosfera_project.servicios.persistencia import crear_base

DB = Path(__file__).resolve().parents[1] / "eventos.db"

import logging
MUESTRA_FR = [
    ("reddit_france", "Le prix du Bitcoin devrait atteindre 120 000 dollars en 2026 selon les experts"),
    ("lemonde", "Guerre en Ukraine : l'offensive russe pres de Kharkiv s'intensifie"),
    ("lefigaro", "Elections americaines 2026 : le Senat se polarise avant le vote"),
    ("bfmtv", "Inflation en Europe : la BCE maintient ses taux malgre la hausse des prix"),
    ("reddit_france", "Le CAC 40 bat un record alors que Wall Street rallye sur les resultats IA"),
    ("lequipe", "Equipe de France qualifiee pour la Coupe du Monde 2026 apres une victoire eclatante"),
    ("reddit_crypto_fr", "Ethereum : la mise a jour reduit les frais de gaz et booste la DeFi"),
    ("lemonde", "Poutine ouvre la porte a la negotiation alors que le conflit entre dans sa troisieme annee"),
    ("lefigaro", "Trump devance dans les sondages pour 2026 alors que le Congres est bloque"),
    ("bfmtv", "La Banque Centrale Europeenne alerte sur l'inflation persistante dans la zone euro"),
    ("reddit_france", "Le Dow Jones et le Nasdaq en hausse suite aux espoirs de atterrissage en douceur"),
    ("lequipe", "Les Bleus preparant la Coupe du Monde avec un nouvel effectif"),
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
    for fuente, texto in MUESTRA_FR:
        h = hashlib.sha1(texto.encode("utf-8", errors="ignore")).hexdigest()[:12]
        try:
            conn.execute(
                "INSERT INTO lenguaje_colectivo (fuente, texto, texto_hash, publicado, creado_en, idioma) VALUES (?,?,?,?,?,?)",
                (fuente, texto, h, None, "2026-07-16T00:00:00", "fr"),
            )
            count += 1
        except sqlite3.IntegrityError as exc:
            logging.warning("documento duplicado o conflicto, se omite: %s", exc)
            pass
    conn.commit()
    conn.close()
    print(f"Ingeridos {count} docs FR")


if __name__ == "__main__":
    ingerir()
