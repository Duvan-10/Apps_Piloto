# pyright: reportMissingImports=false
from flask import Flask, render_template, jsonify, request
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
from pathlib import Path
from vigilante_base import analizar_sentimiento_equipo
from historial_base import calcular_efectividad_especifica, obtener_margen_victoria_especifica

BASE_DIR = Path(__file__).resolve().parent
GUI_DIR = BASE_DIR.parent / 'GUI'

app = Flask(__name__, template_folder=str(GUI_DIR), static_folder=str(GUI_DIR), static_url_path='')

# Configuración
API_KEY_FOOTBALL = '49e96d3486e04479b832501523b36827'
IGNORAR_CARPETAS = {'.git', '__pycache__', 'venv'}
_CACHE_EMBLEMAS = {}


def _normalizar_equipo(equipo):
    return {
        'id': equipo.get('id', 0),
        'name': equipo.get('name', 'Desconocido'),
        'crest': equipo.get('crest', ''),
    }


def _normalizar_partido(partido):
    return {
        'id': partido.get('id', 0),
        'utcDate': partido.get('utcDate', ''),
        'homeTeam': _normalizar_equipo(partido.get('homeTeam', {})),
        'awayTeam': _normalizar_equipo(partido.get('awayTeam', {})),
        'sentimiento_home': partido.get('sentimiento_home', 0),
        'sentimiento_away': partido.get('sentimiento_away', 0),
        'margen_victoria_home': partido.get('margen_victoria_home', 0),
        'margen_victoria_away': partido.get('margen_victoria_away', 0),
        'margen_victoria_max': partido.get('margen_victoria_max', 0),
    }


def _obtener_emblema_competicion(codigo_competicion):
    codigo = str(codigo_competicion).strip().upper()
    if not codigo:
        return ''

    if codigo in _CACHE_EMBLEMAS:
        return _CACHE_EMBLEMAS[codigo]

    url = f"https://api.football-data.org/v4/competitions/{codigo}"
    headers = {'X-Auth-Token': API_KEY_FOOTBALL}

    try:
        req = Request(url, headers=headers)
        with urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))

        emblem = str(data.get('emblem', '')).strip()
        _CACHE_EMBLEMAS[codigo] = emblem
        return emblem
    except Exception as e:
        print(f"Error obteniendo emblema de {codigo}: {e}")
        _CACHE_EMBLEMAS[codigo] = ''
        return ''


def _descubrir_torneos():
    torneos = {}

    for carpeta in BASE_DIR.iterdir():
        if not carpeta.is_dir() or carpeta.name in IGNORAR_CARPETAS:
            continue

        config_path = carpeta / 'config.json'

        if not config_path.exists():
            continue

        try:
            with config_path.open('r', encoding='utf-8') as f:
                config = json.load(f)

            torneo_id = str(config.get('id', '')).strip().lower()
            nombre = str(config.get('nombre', '')).strip()
            codigo = str(config.get('codigo', '')).strip().upper()
            aliases = [str(a).strip().lower() for a in config.get('aliases', [])]
            logo = str(config.get('logo', '')).strip() or _obtener_emblema_competicion(codigo)
            idioma = str(config.get('idioma', '')).strip().lower()
            terminos_liga = [str(t).strip() for t in config.get('terminos_liga', []) if str(t).strip()]

            if not torneo_id or not nombre or not codigo:
                continue

            if not idioma:
                idioma = {
                    'PL': 'en',
                    'PD': 'es',
                    'SA': 'it',
                    'BL1': 'de',
                    'FL1': 'fr',
                }.get(codigo, 'en')

            if not terminos_liga:
                terminos_liga = [nombre, codigo]

            torneos[torneo_id] = {
                'id': torneo_id,
                'nombre': nombre,
                'codigo': codigo,
                'logo': logo,
                'aliases': aliases,
                'idioma': idioma,
                'terminos_liga': terminos_liga,
                'carpeta': carpeta,
            }
        except Exception as e:
            print(f"Error leyendo torneo en {carpeta.name}: {e}")

    return torneos


def _mapa_alias_torneos(torneos):
    alias_map = {}
    for torneo_id, torneo in torneos.items():
        alias_map[torneo_id] = torneo_id
        alias_map[torneo['codigo'].lower()] = torneo_id
        for alias in torneo.get('aliases', []):
            alias_map[alias] = torneo_id
    return alias_map


TORNEOS = _descubrir_torneos()
ALIASES_TORNEOS = _mapa_alias_torneos(TORNEOS)


def _torneo_por_defecto():
    if 'premier' in TORNEOS:
        return 'premier'
    return next(iter(TORNEOS.keys()), None)


def _resolver_torneo(torneo_raw):
    default_torneo = _torneo_por_defecto()
    if not default_torneo:
        return None

    clave = (torneo_raw or default_torneo).strip().lower()
    torneo_id = ALIASES_TORNEOS.get(clave, default_torneo)
    return TORNEOS.get(torneo_id)


def obtener_proxima_fecha(codigo_torneo):
    url = f"https://api.football-data.org/v4/competitions/{codigo_torneo}/matches"
    headers = {'X-Auth-Token': API_KEY_FOOTBALL}
    params = {'status': 'SCHEDULED'}

    try:
        query = urlencode(params)
        full_url = f"{url}?{query}"
        req = Request(full_url, headers=headers)
        with urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))

        matches = data.get('matches', [])
        if matches:
            jornada_actual = matches[0].get('matchday')
            return [m for m in matches if m.get('matchday') == jornada_actual]
        return []
    except Exception as e:
        print(f"Error al conectar con la API ({codigo_torneo}): {e}")
        return []


def _parsear_umbral_margen(valor_margen):
    if valor_margen in (None, '', False):
        return None

    try:
        umbral = float(valor_margen)
    except (TypeError, ValueError):
        return None

    if umbral < 0:
        return None

    return umbral


def obtener_partidos_enriquecidos(torneo, umbral_margen=None):
    if not torneo:
        return []

    partidos = obtener_proxima_fecha(torneo['codigo'])
    partidos_filtrados = []

    for partido in partidos:
        nombre_home = partido.get('homeTeam', {}).get('name', 'Local')
        nombre_away = partido.get('awayTeam', {}).get('name', 'Visitante')
        home_id = partido.get('homeTeam', {}).get('id', 0)
        away_id = partido.get('awayTeam', {}).get('id', 0)

        if umbral_margen is not None:
            margen = obtener_margen_victoria_especifica(API_KEY_FOOTBALL, partido.get('id', 0), home_id, away_id)
            partido['margen_victoria_home'] = margen.get('home', 0)
            partido['margen_victoria_away'] = margen.get('away', 0)
            partido['margen_victoria_max'] = margen.get('max', 0)

            if float(partido['margen_victoria_max'] or 0) < umbral_margen:
                continue

        try:
            partido['sentimiento_home'] = analizar_sentimiento_equipo(
                nombre_home,
                liga=torneo['nombre'],
                idioma=torneo['idioma'],
                terminos_liga=torneo['terminos_liga'],
                etiqueta=torneo['nombre'],
            )
            partido['sentimiento_away'] = analizar_sentimiento_equipo(
                nombre_away,
                liga=torneo['nombre'],
                idioma=torneo['idioma'],
                terminos_liga=torneo['terminos_liga'],
                etiqueta=torneo['nombre'],
            )
            print(
                f"[vigilante-{torneo['id']}] {nombre_home} -> {partido['sentimiento_home']}, "
                f"{nombre_away} -> {partido['sentimiento_away']}"
            )
        except Exception as e:
            print(f"Vigilante falló en {torneo['nombre']}: {e}")
            partido['sentimiento_home'] = 0
            partido['sentimiento_away'] = 0

        partidos_filtrados.append(partido)

    return [_normalizar_partido(partido) for partido in partidos_filtrados]


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/torneos')
def api_torneos():
    return jsonify([
        {
            'id': torneo['id'],
            'nombre': torneo['nombre'],
            'codigo': torneo['codigo'],
            'logo': torneo['logo'],
        }
        for torneo in TORNEOS.values()
    ])


@app.route('/api/partidos')
def api_partidos():
    torneo = _resolver_torneo(request.args.get('torneo'))
    umbral_margen = _parsear_umbral_margen(request.args.get('margen'))
    return jsonify(obtener_partidos_enriquecidos(torneo, umbral_margen=umbral_margen))


@app.route('/index.html')
def home_index():
    return home()


@app.route('/predicciones')
def predicciones():
    return home()


@app.route('/estadisticas')
def estadisticas():
    return home()


@app.route('/api/historial/<int:match_id>/<int:home_id>/<int:away_id>')
def api_historial(match_id, home_id, away_id):
    torneo = _resolver_torneo(request.args.get('torneo'))
    if not torneo:
        return jsonify({"home": 0, "away": 0, "total": 0, "error": "No hay torneos configurados"})

    try:
        resultado = calcular_efectividad_especifica(API_KEY_FOOTBALL, match_id, home_id, away_id)

        if not resultado or not isinstance(resultado, dict):
            return jsonify({"home": 0, "away": 0, "total": 0})

        home = resultado.get('home', 0)
        away = resultado.get('away', 0)
        total = resultado.get('total', 0)

        print(
            f"[historial-{torneo['id']}] match={match_id} home={home_id} away={away_id} "
            f"-> home%={home} away%={away} total={total}"
        )
        return jsonify({"home": home, "away": away, "total": total})
    except Exception as e:
        print(f"[historial-{torneo['id']}][error] {e}")
        return jsonify({"home": 0, "away": 0, "total": 0, "error": str(e)})


if __name__ == '__main__':
    app.run(debug=True)
