# pyright: reportMissingImports=false
from flask import Flask, render_template, jsonify
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

# Importamos tus módulos personalizados
from vigilante import analizar_sentimiento_equipo
from historial import calcular_efectividad_especifica  # Asegúrate de haber creado este archivo

app = Flask(__name__, template_folder='../GUI')

# Configuración
API_KEY_FOOTBALL = '49e96d3486e04479b832501523b36827'

def obtener_proxima_fecha():
    url = "https://api.football-data.org/v4/competitions/PL/matches"
    headers = { 'X-Auth-Token': API_KEY_FOOTBALL }
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
        return []

@app.route('/')
def home():
    # 1. Obtenemos los partidos
    partidos = obtener_proxima_fecha()
    
    # 2. El Vigilante analiza el ánimo (sentimiento) de cada equipo
    for partido in partidos:
        nombre_home = partido['homeTeam']['name']
        nombre_away = partido['awayTeam']['name']
        
        try:
            partido['sentimiento_home'] = analizar_sentimiento_equipo(nombre_home)
            partido['sentimiento_away'] = analizar_sentimiento_equipo(nombre_away)
        except Exception as e:
            print(f"Vigilante falló: {e}")
            partido['sentimiento_home'] = 0
            partido['sentimiento_away'] = 0

    return render_template('index.html', partidos=partidos)

# --- NUEVA RUTA PARA EL HISTORIAL ESPECÍFICO (API) ---
@app.route('/api/historial/<int:match_id>/<int:home_id>/<int:away_id>')
def api_historial(match_id, home_id, away_id):
    """
    Ruta que devuelve el porcentaje de efectividad histórica 
    basado puramente en la condición Local/Visitante.
    """
    try:
        resultado = calcular_efectividad_especifica(API_KEY_FOOTBALL, match_id, home_id, away_id)
        if resultado:
            return jsonify(resultado)
        return jsonify({"error": "No hay datos suficientes"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)