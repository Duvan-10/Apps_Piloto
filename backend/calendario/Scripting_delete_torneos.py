"""
===========================================================
SCRIPTING DELETE TORNEOS + COMPACTAR IDS
Ubicación: backend/calendario/Scripting_delete_torneos.py
===========================================================
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "futbol.db")

print(f"📂 Usando base de datos: {DB_PATH}\n")

def delete_tournament(torneo_id):
    """Elimina un torneo y sus equipos/partidos asociados."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Primero eliminar partidos asociados
    cur.execute("DELETE FROM matches WHERE torneo_id = ?;", (torneo_id,))
    # Luego eliminar equipos asociados
    cur.execute("DELETE FROM teams WHERE torneo_id = ?;", (torneo_id,))
    # Finalmente eliminar el torneo
    cur.execute("DELETE FROM tournaments WHERE id = ?;", (torneo_id,))

    conn.commit()
    conn.close()
    print(f"🗑️ Torneo con ID {torneo_id} y sus dependencias eliminados correctamente.")

def compact_ids():
    """Reorganiza los IDs de tournaments, teams y matches consecutivamente desde 1."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Compactar tournaments
    cur.execute("SELECT id FROM tournaments ORDER BY id;")
    ids = [row[0] for row in cur.fetchall()]
    nuevo_id = 1
    for viejo_id in ids:
        cur.execute("UPDATE tournaments SET id = ? WHERE id = ?", (nuevo_id, viejo_id))
        cur.execute("UPDATE teams SET torneo_id = ? WHERE torneo_id = ?", (nuevo_id, viejo_id))
        cur.execute("UPDATE matches SET torneo_id = ? WHERE torneo_id = ?", (nuevo_id, viejo_id))
        nuevo_id += 1

    # Compactar teams
    cur.execute("SELECT id FROM teams ORDER BY id;")
    ids = [row[0] for row in cur.fetchall()]
    nuevo_id = 1
    for viejo_id in ids:
        cur.execute("UPDATE teams SET id = ? WHERE id = ?", (nuevo_id, viejo_id))
        cur.execute("UPDATE matches SET home_team_id = ? WHERE home_team_id = ?", (nuevo_id, viejo_id))
        cur.execute("UPDATE matches SET away_team_id = ? WHERE away_team_id = ?", (nuevo_id, viejo_id))
        nuevo_id += 1

    # Compactar matches
    cur.execute("SELECT id FROM matches ORDER BY id;")
    ids = [row[0] for row in cur.fetchall()]
    nuevo_id = 1
    for viejo_id in ids:
        cur.execute("UPDATE matches SET id = ? WHERE id = ?", (nuevo_id, viejo_id))
        nuevo_id += 1

    # Reiniciar secuencia de autoincremento
    try:
        cur.execute("DELETE FROM sqlite_sequence WHERE name='tournaments';")
        cur.execute("DELETE FROM sqlite_sequence WHERE name='teams';")
        cur.execute("DELETE FROM sqlite_sequence WHERE name='matches';")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()
    print("✅ IDs compactados y reiniciados en tournaments, teams y matches.")

if __name__ == "__main__":
    torneo_id = int(input("Ingrese el ID del torneo a eliminar: "))
    delete_tournament(torneo_id)
    compact_ids()
