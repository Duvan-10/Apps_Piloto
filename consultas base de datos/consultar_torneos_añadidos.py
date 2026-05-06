import sqlite3
import os

# Ruta absoluta al futbol.db en la raíz del proyecto
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "futbol.db")

print(f"📂 Usando base de datos: {DB_PATH}\n")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("=== TORNEOS GUARDADOS ===")
try:
    cur.execute("SELECT id, nombre, escudo, fuente_url FROM tournaments;")
    torneos = cur.fetchall()
    if torneos:
        for torneo in torneos:
            print(f"ID: {torneo[0]} | Nombre: {torneo[1]} | Escudo: {torneo[2]} | Fuente: {torneo[3]}")
    else:
        print("⚠️ No hay torneos guardados en la base de datos.")
except Exception as e:
    print(f"⚠️ Error al consultar torneos: {e}")

conn.close()
