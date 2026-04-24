# pyright: reportMissingImports=false
from flask import Flask, render_template
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

app = Flask(__name__, template_folder='../GUI')

def obtener_proxima_fecha():
    # URL para obtener todos los partidos de la Premier League (PL)
    url = "https://api.football-data.org/v4/competitions/PL/matches"
    
    # IMPORTANTE: Para que esto funcione con datos reales, 
    # regístrate gratis en football-data.org y pega tu clave aquí.
    headers = { 'X-Auth-Token': '49e96d3486e04479b832501523b36827' }
    
    # Filtramos por partidos programados (SCHEDULED)
    params = { 'status': 'SCHEDULED' }
    
    try:
        # Si aún no tienes API KEY, esta parte fallará y saltará al 'except'
        query = urlencode(params)
        full_url = f"{url}?{query}"
        req = Request(full_url, headers=headers)
        with urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
        matches = data.get('matches', [])
        
        if matches:
            # Tomamos el número de la jornada del primer partido que encontremos
            jornada_actual = matches[0].get('matchday')
            # Filtramos todos los partidos que pertenezcan a esa misma jornada
            proximos_partidos = [m for m in matches if m.get('matchday') == jornada_actual]
            return proximos_partidos
        return []
    
    except Exception as e:
        print(f"Error al conectar con la API: {e}")
        # DATOS DE PRUEBA AMPLIADOS (En caso de que no tengas la API KEY aún)
        # Esto simula una jornada completa para que veas cómo se ve la interfaz
        return [
            {'homeTeam': {'name': 'Arsenal', 'crest': 'https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg'}, 'awayTeam': {'name': 'Newcastle', 'crest': 'https://upload.wikimedia.org/wikipedia/en/5/56/Newcastle_United_Logo.svg'}, 'utcDate': '2026-04-25'},
            {'homeTeam': {'name': 'Man. United', 'crest': 'https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg'}, 'awayTeam': {'name': 'Brentford', 'crest': 'https://upload.wikimedia.org/wikipedia/en/2/2a/Brentford_FC_crest.svg'}, 'utcDate': '2026-04-27'},
            {'homeTeam': {'name': 'Liverpool', 'crest': 'https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg'}, 'awayTeam': {'name': 'Everton', 'crest': 'https://upload.wikimedia.org/wikipedia/en/7/7c/Everton_FC_logo.svg'}, 'utcDate': '2026-04-28'},
            {'homeTeam': {'name': 'Manchester City', 'crest': 'https://upload.wikimedia.org/wikipedia/en/eb/eb/Manchester_City_FC_badge.svg'}, 'awayTeam': {'name': 'Aston Villa', 'crest': 'https://upload.wikimedia.org/wikipedia/en/f/f9/Aston_Villa_FC_crest_%282016%29.svg'}, 'utcDate': '2026-04-28'},
            {'homeTeam': {'name': 'Chelsea', 'crest': 'https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg'}, 'awayTeam': {'name': 'West Ham', 'crest': 'https://upload.wikimedia.org/wikipedia/en/c/c2/West_Ham_United_FC_logo.svg'}, 'utcDate': '2026-04-29'}
        ]

@app.route('/')
def home():
    partidos = obtener_proxima_fecha()
    return render_template('index.html', partidos=partidos)

if __name__ == '__main__':
    app.run(debug=True)