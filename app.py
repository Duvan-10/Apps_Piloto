import json
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).resolve().parent
CHAMPIONS_DATA_CANDIDATES = [
    BASE_DIR / "Backend" / "data" / "champions_raw.json",
    BASE_DIR / "Backend" / "Backend" / "data" / "champions_raw.json",
]


# ==========================================================
# CONFIGURACIÓN MAESTRA DE TORNEOS
# ==========================================================
# ## AÑADE AQUÍ NUEVOS TORNEOS SIGUIENDO ESTE FORMATO ##
TORNEOS_CONFIG = {
    "champions": {
        "nombre": "UEFA Champions League",
        "api_id": 2001,
        "url_logo": "https://logodownload.org/wp-content/uploads/2018/09/uefa-champions-league-logo-0.png",
        "url_logo_fallback": "https://crests.football-data.org/CL.png",
    },
}

API_SPORTS_TEAM_IDS = {
    "arsenal": 42,
    "arsenal fc": 42,
    "club atletico de madrid": 530,
    "club atlético de madrid": 530,
    "atletico madrid": 530,
    "atleti": 530,
    "fc bayern munchen": 157,
    "fc bayern münchen": 157,
    "bayern munich": 157,
    "bayern": 157,
    "paris saint germain fc": 85,
    "paris saint-germain fc": 85,
    "paris saint germain": 85,
    "psg": 85,
}


def _normalizar_texto(texto: str) -> str:
    texto_normalizado = unicodedata.normalize("NFKD", texto or "")
    texto_sin_acentos = "".join(caracter for caracter in texto_normalizado if not unicodedata.combining(caracter))
    return " ".join(texto_sin_acentos.lower().strip().split())


def _obtener_ruta_datos() -> Path | None:
    for candidate in CHAMPIONS_DATA_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def _obtener_logo_api_sports(nombre_equipo: str | None) -> str:
    nombre_normalizado = _normalizar_texto(nombre_equipo or "")
    api_sports_id = API_SPORTS_TEAM_IDS.get(nombre_normalizado)
    if api_sports_id:
        return f"https://media.api-sports.io/football/teams/{api_sports_id}.png"
    return "https://via.placeholder.com/120x120?text=Club"


def _parsear_fecha_iso(fecha_iso: str | None) -> datetime | None:
    if not fecha_iso:
        return None

    try:
        return datetime.fromisoformat(fecha_iso.replace("Z", "+00:00"))
    except ValueError:
        return None


def _cargar_partidos_champions() -> list[dict]:
    ruta_datos = _obtener_ruta_datos()
    if ruta_datos is None:
        return []

    ahora = datetime.now(timezone.utc)

    with ruta_datos.open("r", encoding="utf-8") as archivo:
        partidos = json.load(archivo)

    partidos_filtrados = []
    for partido in partidos:
        competition = partido.get("competition") or {}
        home_team = partido.get("homeTeam") or {}
        away_team = partido.get("awayTeam") or {}

        if competition.get("id") != TORNEOS_CONFIG["champions"]["api_id"]:
            continue
        if not home_team.get("name") or not away_team.get("name"):
            continue
        if partido.get("status") != "TIMED":
            continue
        if partido.get("stage") != "SEMI_FINALS":
            continue

        fecha_partido = _parsear_fecha_iso(partido.get("utcDate"))
        if fecha_partido is None or fecha_partido <= ahora:
            continue

        partidos_filtrados.append(
            {
                "id": partido.get("id"),
                "equipo_local": home_team.get("name"),
                "equipo_visitante": away_team.get("name"),
                "logo_local": _obtener_logo_api_sports(home_team.get("name")),
                "logo_visitante": _obtener_logo_api_sports(away_team.get("name")),
                "fecha": partido.get("utcDate"),
                "estado": partido.get("status"),
                "jornada": partido.get("matchday"),
                "etapa": partido.get("stage"),
            }
        )

    partidos_filtrados.sort(key=lambda item: item.get("fecha") or "")
    return partidos_filtrados


@app.route("/api/torneos", methods=["GET"])
def get_tournaments():
    lista = [
        {
            "slug": slug,
            "nombre": config["nombre"],
            "api_id": config["api_id"],
            "url_logo": config["url_logo"],
            "url_logo_fallback": config.get("url_logo_fallback", config["url_logo"]),
        }
        for slug, config in TORNEOS_CONFIG.items()
    ]
    return jsonify(lista)


@app.route("/api/tournaments", methods=["GET"])
def get_tournaments_legacy():
    return get_tournaments()


@app.route("/api/partidos", methods=["GET"])
def get_partidos_default():
    return jsonify(_cargar_partidos_champions())


@app.route("/api/partidos/<int:torneo_id>", methods=["GET"])
def get_partidos(torneo_id):
    torneo_config = next((config for config in TORNEOS_CONFIG.values() if config["api_id"] == torneo_id), None)
    if torneo_config is None:
        return jsonify({"error": "Torneo no disponible"}), 404

    if torneo_id != TORNEOS_CONFIG["champions"]["api_id"]:
        return jsonify([])

    return jsonify(_cargar_partidos_champions())


if __name__ == "__main__":
    app.run(debug=True, port=5000)