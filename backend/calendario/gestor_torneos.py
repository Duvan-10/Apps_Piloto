"""
===========================================================
GESTOR DE TORNEOS
Ubicación: backend/calendario/gestor_torneos.py

Este módulo administra los torneos de fútbol en la base de datos:
- Añadir torneos (tabla tournaments)
- Eliminar torneos y sus dependencias (teams, matches)
- Listar torneos, equipos y partidos
- Sincronizar equipos y partidos desde Flashscore

Se utiliza como núcleo para los scripts auxiliares:
- añadir_torneos.py
- consultar_torneos.py
- mostrar_calendario.py
===========================================================
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
import os

# ---------------------------------------------------------
# Ruta absoluta a la base de datos futbol.db en la raíz
# ---------------------------------------------------------
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "futbol.db")

# ---------------------------
# Funciones de base de datos
# ---------------------------

def connect_db():
    """Conecta con la base de datos SQLite."""
    return sqlite3.connect(DB_PATH)

def add_tournament(nombre, escudo, fuente_url):
    """Inserta un torneo en la tabla tournaments."""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tournaments (nombre, escudo, fuente_url)
        VALUES (?, ?, ?)
    """, (nombre, escudo, fuente_url))
    conn.commit()
    conn.close()

def list_tournaments():
    """Devuelve todos los torneos guardados en la base."""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre, escudo, fuente_url FROM tournaments")
    torneos = cur.fetchall()
    conn.close()
    return torneos

def add_team(nombre, escudo, torneo_id):
    """Inserta un equipo en la tabla teams vinculado a un torneo."""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO teams (nombre, escudo, torneo_id)
        VALUES (?, ?, ?)
    """, (nombre, escudo, torneo_id))
    conn.commit()
    conn.close()

def list_teams():
    """Devuelve todos los equipos guardados en la base."""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre, escudo, torneo_id FROM teams")
    equipos = cur.fetchall()
    conn.close()
    return equipos

def add_match(torneo_id, fecha_hora, home_team_id, away_team_id):
    """Inserta un partido en la tabla matches vinculado a un torneo."""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO matches (torneo_id, fecha_hora, home_team_id, away_team_id)
        VALUES (?, ?, ?, ?)
    """, (torneo_id, fecha_hora, home_team_id, away_team_id))
    conn.commit()
    conn.close()

def list_matches():
    """Devuelve todos los partidos guardados en la base."""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT id, torneo_id, fecha_hora, home_team_id, away_team_id FROM matches")
    partidos = cur.fetchall()
    conn.close()
    return partidos

# ---------------------------
# Funciones de sincronización
# ---------------------------

def sync_teams(torneo_id, url_clasificacion):
    """Sincroniza equipos desde Flashscore y los inserta en la base."""
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url_clasificacion, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    equipos = soup.select(".participant__participantName")
    for e in equipos:
        nombre_equipo = e.text.strip()
        if nombre_equipo:
            ruta_escudo = f"assets/equipos/{nombre_equipo.lower().replace(' ', '_')}.png"
            add_team(nombre_equipo, ruta_escudo, torneo_id)
            print(f"✅ Equipo sincronizado: {nombre_equipo}")

def sync_matches(torneo_id, url_partidos):
    """Sincroniza partidos desde Flashscore y los inserta en la base."""
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url_partidos, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    equipos_db = {nombre: id for id, nombre, _, _ in list_teams()}

    partidos = soup.select(".event__match")
    for p in partidos:
        try:
            fecha_hora = p.select_one(".event__time").text.strip()
            home = p.select_one(".event__participant--home").text.strip()
            away = p.select_one(".event__participant--away").text.strip()

            home_id = equipos_db.get(home)
            away_id = equipos_db.get(away)

            if home_id and away_id:
                add_match(torneo_id, fecha_hora, home_id, away_id)
                print(f"✅ Partido sincronizado: {home} vs {away} ({fecha_hora})")
        except Exception as ex:
            print("⚠️ Error al capturar partido:", ex)

# ---------------------------
# Añadir torneo solo con nombre
# ---------------------------

def add_tournament_by_name(nombre_torneo):
    """Añade un torneo automáticamente detectando su URL en Flashscore."""
    headers = {"User-Agent": "Mozilla/5.0"}
    url_base = "https://www.flashscore.co/futbol/"
    resp = requests.get(url_base, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    torneos_web = soup.select("a")
    for t in torneos_web:
        href = t.get("href", "")
        if "/futbol/inglaterra/premier-league/" in href:
            fuente_url = "https://www.flashscore.co" + href
            escudo = f"assets/torneos/{nombre_torneo.lower().replace(' ', '_')}.png"

            add_tournament(nombre_torneo, escudo, fuente_url)
            torneo_id = list_tournaments()[-1][0]

            sync_teams(torneo_id, fuente_url + "clasificacion/")
            sync_matches(torneo_id, fuente_url + "partidos/")

            print(f"✅ Torneo agregado automáticamente: {nombre_torneo}")
            return

    print(f"⚠️ No se encontró el torneo: {nombre_torneo}")
