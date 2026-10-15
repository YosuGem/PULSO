"""Sistema de plugins para fuentes de ingesta."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Protocol


@dataclass
class Item:
    titulo: str
    enlace: str
    publicado: str
    fuente: str
    categorias: str = ""


class Fuente(Protocol):
    nombre: str
    def obtener(self, limit: int = 20) -> List[Item]: ...


class RSSFuente:
    def __init__(self, nombre: str, url: str) -> None:
        self.nombre = nombre
        self.url = url

    def obtener(self, limit: int = 20) -> List[Item]:  # stub real delegable a rss.py
        return []


class OfflineFuente:
    def __init__(self, nombre: str, ruta: str) -> None:
        self.nombre = nombre
        self.ruta = ruta

    def obtener(self, limit: int = 20) -> List[Item]:
        return []
