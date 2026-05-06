import sqlite3

DB_PATH = "futbol.db"
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 1. Crear nueva tabla tournaments con estructura correcta
cur.execute("""
CREATE TABLE IF NOT EXISTS tournaments_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    escudo TEXT,
    fuente_url TEXT
)
""")

# Copiar datos de la vieja
cur.execute("INSERT INTO tournaments_new (id, nombre, escudo) SELECT id, name, emblem FROM tournaments;")

# 2. Crear nueva tabla teams con estructura correcta
cur.execute("""
CREATE TABLE IF NOT EXISTS teams_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    escudo TEXT,
    torneo_id INTEGER,
    FOREIGN KEY (torneo_id) REFERENCES tournaments_new(id)
)
""")

cur.execute("INSERT INTO teams_new (id, nombre, escudo) SELECT id, name, emblem FROM teams;")

# 3. Crear nueva tabla matches con estructura correcta
cur.execute("""
CREATE TABLE IF NOT EXISTS matches_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    torneo_id INTEGER,
    fecha_hora TEXT,
    home_team_id INTEGER,
    away_team_id INTEGER,
    FOREIGN KEY (torneo_id) REFERENCES tournaments_new(id),
    FOREIGN KEY (home_team_id) REFERENCES teams_new(id),
    FOREIGN KEY (away_team_id) REFERENCES teams_new(id)
)
""")

cur.execute("INSERT INTO matches_new (id, torneo_id, fecha_hora, home_team_id, away_team_id) SELECT id, tournament_id, date_time, home_team_id, away_team_id FROM matches;")

# 4. Borrar tablas viejas y renombrar nuevas
cur.execute("DROP TABLE tournaments;")
cur.execute("ALTER TABLE tournaments_new RENAME TO tournaments;")

cur.execute("DROP TABLE teams;")
cur.execute("ALTER TABLE teams_new RENAME TO teams;")

cur.execute("DROP TABLE matches;")
cur.execute("ALTER TABLE matches_new RENAME TO matches;")

conn.commit()
conn.close()

print("🎉 Migración completada. La base ahora tiene columnas en español y coincide con el código.")
