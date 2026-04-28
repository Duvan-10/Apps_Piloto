from urllib.request import Request, urlopen
import json

_CACHE_HISTORIAL = {}


def _clave_historial(match_id, home_id, away_id):
    return f"{int(match_id)}|{int(home_id)}|{int(away_id)}"


def calcular_efectividad_especifica(api_key, match_id, home_id, away_id):
    clave = _clave_historial(match_id, home_id, away_id)
    if clave in _CACHE_HISTORIAL:
        return _CACHE_HISTORIAL[clave]

    url = f"https://api.football-data.org/v4/matches/{match_id}/head2head?limit=50"
    headers = {'X-Auth-Token': api_key}

    try:
        req = Request(url, headers=headers)
        with urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))

        historial = data.get('matches', [])
        partidos_en_condicion = [
            m for m in historial
            if m['homeTeam']['id'] == home_id and m['awayTeam']['id'] == away_id
        ]

        total = len(partidos_en_condicion)
        if total == 0:
            return {"home": 0, "away": 0, "total": 0}

        victorias_home = len([m for m in partidos_en_condicion if m['score']['winner'] == 'HOME_TEAM'])
        victorias_away = len([m for m in partidos_en_condicion if m['score']['winner'] == 'AWAY_TEAM'])

        resultado = {
            "home": round((victorias_home / total) * 100, 1),
            "away": round((victorias_away / total) * 100, 1),
            "total": total,
        }
        _CACHE_HISTORIAL[clave] = resultado
        return resultado
    except Exception as e:
        print(f"Error en historial base: {e}")
        return None


def obtener_margen_victoria_especifica(api_key, match_id, home_id, away_id):
    resultado = calcular_efectividad_especifica(api_key, match_id, home_id, away_id)
    if not resultado or not isinstance(resultado, dict):
        return {"home": 0, "away": 0, "total": 0, "max": 0}

    home = float(resultado.get('home', 0) or 0)
    away = float(resultado.get('away', 0) or 0)
    total = int(resultado.get('total', 0) or 0)
    margen_maximo = max(home, away)

    return {
        "home": round(home, 1),
        "away": round(away, 1),
        "total": total,
        "max": round(margen_maximo, 1),
    }