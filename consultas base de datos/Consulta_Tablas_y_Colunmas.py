import sqlite3
import os

# Ruta absoluta al futbol.db en la raíz del proyecto
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "futbol.db")

print(f"📂 Usando base de datos: {DB_PATH}\n")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Listar todas las tablas
print("=== Tablas existentes ===")
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tablas = [t[0] for t in cur.fetchall()]
for tabla in tablas:
    print(f"- {tabla}")

print("\n=== Columnas por tabla ===")
for tabla in tablas:
    print(f"\nTabla: {tabla}")
    cur.execute(f"PRAGMA table_info({tabla});")
    columnas = cur.fetchall()
    if columnas:
        for col in columnas:
            print(f"- {col[1]} ({col[2]})")
    else:
        print("⚠️ No tiene columnas definidas")

conn.close()
