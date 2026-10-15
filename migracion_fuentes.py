#!/usr/bin/env python3
"""
Migración: Crear tabla fuentes en eventos.db
Ejecutar para agregar soporte a /api/fuentes
"""
import sqlite3
from pathlib import Path

# Se usa la base del propio paquete, no una ruta fija del equipo donde se
# desarrollo. Así el script funciona en cualquier instalación y no se
# publica una ruta personal.
_DB_PROPIA = Path(__file__).resolve().parent / "noosfera_project" / "eventos.db"
DB_PATH = _DB_PROPIA if _DB_PROPIA.exists() else _DB_PROPIA

def main():
    print("=" * 50)
    print("MIGRACIÓN: Crear tabla fuentes")
    print("=" * 50)
    
    if not DB_PATH.exists():
        print(f"❌ Error: Base de datos no encontrada en {DB_PATH}")
        return False
    
    try:
        con = sqlite3.connect(str(DB_PATH))
        cursor = con.cursor()
        
        # Verificar si ya existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fuentes'")
        if cursor.fetchone():
            print("✅ Tabla fuentes ya existe")
            cursor.execute("SELECT COUNT(*) FROM fuentes")
            count = cursor.fetchone()[0]
            print(f"   Registros: {count}")
            con.close()
            return True
        
        # Crear tabla
        cursor.execute("""
            CREATE TABLE fuentes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                url TEXT NOT NULL,
                tipo TEXT DEFAULT 'rss',
                idioma TEXT DEFAULT 'es',
                score REAL DEFAULT 0.0,
                ultima_actualizacion TEXT,
                activo INTEGER DEFAULT 1
            )
        """)
        print("✅ Tabla fuentes creada")
        
        # Insertar datos por defecto
        fuentes = [
            ("Hacker News", "https://news.ycombinator.com/rss", "rss", "en", 0.8, 1),
            ("Reddit", "https://www.reddit.com/.rss", "social", "en", 0.7, 1),
            ("Telegram", "telegram://", "social", "es", 0.6, 1),
            ("Lemmy", "https://lemmy.world", "social", "es", 0.5, 1),
            ("4chan", "https://boards.4chan.org/", "social", "en", 0.4, 1),
        ]
        
        cursor.executemany(
            "INSERT INTO fuentes (nombre, url, tipo, idioma, score, activo) VALUES (?, ?, ?, ?, ?, ?)",
            fuentes
        )
        con.commit()
        print(f"✅ Insertadas {len(fuentes)} fuentes por defecto")
        
        con.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    main()