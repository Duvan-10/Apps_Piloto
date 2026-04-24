from urllib.request import Request, urlopen
import json

def calcular_efectividad_especifica(api_key, match_id, home_id, away_id):
    url = f"https://api.football-data.org/v4/matches/{match_id}/head2head?limit=50"
    headers = { 'X-Auth-Token': api_key }
    
    try:
        req = Request(url, headers=headers)
        with urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        historial = data.get('matches', [])
        
        # FILTRO CRÍTICO: Solo cuando Home fue Home y Away fue Away
        partidos_en_condicion = [
            m for m in historial 
            if m['homeTeam']['id'] == home_id and m['awayTeam']['id'] == away_id
        ]
        
        total = len(partidos_en_condicion)
        if total == 0:
            return {"home": 0, "away": 0, "total": 0}

        victorias_home = len([m for m in partidos_en_condicion if m['score']['winner'] == 'HOME_TEAM'])
        victorias_away = len([m for m in partidos_en_condicion if m['score']['winner'] == 'AWAY_TEAM'])
        
        # Cálculo de efectividad en porcentaje
        efectividad_home = (victorias_home / total) * 100
        efectividad_away = (victorias_away / total) * 100
        
        return {
            "home": round(efectividad_home, 1),
            "away": round(efectividad_away, 1),
            "total": total
        }
    except Exception as e:
        print(f"Error en historial: {e}")
        return None