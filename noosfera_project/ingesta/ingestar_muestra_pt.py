"""Ingesta de muestra PT para rollout multilingüe (Bloque A)."""
from __future__ import annotations

import sqlite3
import hashlib
from pathlib import Path

from noosfera_project.servicios.persistencia import crear_base

DB = Path(__file__).resolve().parents[1] / "eventos.db"

import logging
MUESTRA_PT = [
    ("reddit_br", "O preco do Bitcoin deve chegar a 120.000 dolares em 2026 segundo especialistas"),
    ("folha", "Guerra na Ucrania: ofensiva russa perto de Kharkiv se intensifica"),
    ("estadao", "Eleicoes americanas 2026: o Senado se polariza antes da votacao"),
    ("g1", "Inflacao na Europa: o BCE mantem juros apesar da alta de precos"),
    ("reddit_br", "O Ibovespa bate recorde enquanto Wall Street rally apos resultados de IA"),
    ("ge", "Selecao brasileira classificada para a Copa do Mundo 2026 apos vitoria"),
    ("reddit_crypto_br", "Ethereum: atualizacao reduz taxas de gas e impulsiona DeFi"),
    ("folha", "Putin abre porta para negociacao enquanto conflito entra no terceiro ano"),
    ("estadao", "Trump lidera pesquisas para 2026 enquanto Congresso esta bloqueado"),
    ("g1", "Banco Central Europeu alerta para inflacao persistente na zona do euro"),
    ("reddit_br", "Dow Jones e Nasdaq sobem apos expectativas de pouso suave"),
    ("ge", "Selecao prepara Copa do Mundo com novo elenco"),
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
    for fuente, texto in MUESTRA_PT:
        h = hashlib.sha1(texto.encode("utf-8", errors="ignore")).hexdigest()[:12]
        try:
            conn.execute(
                "INSERT INTO lenguaje_colectivo (fuente, texto, texto_hash, publicado, creado_en, idioma) VALUES (?,?,?,?,?,?)",
                (fuente, texto, h, None, "2026-07-16T00:00:00", "pt"),
            )
            count += 1
        except sqlite3.IntegrityError as exc:
            logging.warning("documento duplicado o conflicto, se omite: %s", exc)
            pass
    conn.commit()
    conn.close()
    print(f"Ingeridos {count} docs PT")


if __name__ == "__main__":
    ingerir()
