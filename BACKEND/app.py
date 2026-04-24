# pyright: reportMissingImports=false
from flask import Flask, render_template
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
from vigilante import analizar_sentimiento_equipo

app = Flask(__name__, template_folder='../GUI')

def obtener_proxima_fecha():
    url = "https://api.football-data.org/v4/competitions/PL/matches"
    headers = { 'X-Auth-Token': '49e96d3486e04479b832501523b36827' }
    params = { 'status': 'SCHEDULED' }
    
    try:
        query = urlencode(params)
        full_url = f"{url}?{query}"
        req = Request(full_url, headers=headers)
        with urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
        matches = data.get('matches', [])
        
        if matches:
            jornada_actual = matches[0].get('matchday')
            proximos_partidos = [m for m in matches if m.get('matchday') == jornada_actual]
            return proximos_partidos
        return []
    
    except Exception as e:
        print(f"Error al conectar con la API: {e}")
        return [
            {'homeTeam': {'name': 'Arsenal', 'crest': 'https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg'}, 'awayTeam': {'name': 'Newcastle', 'crest': 'https://upload.wikimedia.org/wikipedia/en/5/56/Newcastle_United_Logo.svg'}, 'utcDate': '2026-04-25'},
            {'homeTeam': {'name': 'Man. United', 'crest': 'https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg'}, 'awayTeam': {'name': 'Brentford', 'crest': 'https://upload.wikimedia.org/wikipedia/en/2/2a/Brentford_FC_crest.svg'}, 'utcDate': '2026-04-27'},
            {'homeTeam': {'name': 'Liverpool', 'crest': 'https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg'}, 'awayTeam': {'name': 'Everton', 'crest': 'https://upload.wikimedia.org/wikipedia/en/7/7c/Everton_FC_logo.svg'}, 'utcDate': '2026-04-28'},
            {'homeTeam': {'name': 'Manchester City', 'crest': 'https://upload.wikimedia.org/wikipedia/en/eb/eb/Manchester_City_FC_badge.svg'}, 'awayTeam': {'name': 'Aston Villa', 'crest': 'https://upload.wikimedia.org/wikipedia/en/f/f9/Aston_Villa_FC_crest_%282016%29.svg'}, 'utcDate': '2026-04-28'},
            {'homeTeam': {'name': 'Chelsea', 'crest': 'https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg'}, 'awayTeam': {'name': 'West Ham', 'crest': 'https://upload.wikimedia.org/wikipedia/en/c/c2/West_Ham_United_FC_logo.svg'}, 'utcDate': '2026-04-29'}
        ]

@app.route('/')
def home():
    # 1. Obtenemos los partidos
    partidos = obtener_proxima_fecha()
    
    # 2. El Vigilante analiza cada partido antes de enviarlo a la GUI
    for partido in partidos:
        # Extraemos nombres de equipos
        nombre_home = partido['homeTeam']['name']
        nombre_away = partido['awayTeam']['name']
        
        # Llamamos a la función de tu archivo vigilante.py
        # Usamos try/except por si la API de noticias falla, que el app no se caiga
        try:
            partido['sentimiento_home'] = analizar_sentimiento_equipo(nombre_home)
            partido['sentimiento_away'] = analizar_sentimiento_equipo(nombre_away)
        except Exception as e:
            print(f"Vigilante falló para {nombre_home} vs {nombre_away}: {e}")
            partido['sentimiento_home'] = 0
            partido['sentimiento_away'] = 0

    # 3. Ahora sí, enviamos los partidos con los datos de sentimiento incluidos
    return render_template('index.html', partidos=partidos)

if __name__ == '__main__':
    app.run(debug=True)