import requests
import json
import os

def get_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def get_news_for_team(team_name):
    config = get_config()
    api_key = config['api_keys']['news_api']
    
    # Filtramos la búsqueda: Nombre del equipo + fútbol + términos clave
    # Buscamos en español e inglés para tener más cobertura de bajas/lesiones
    query = f'"{team_name}" AND (fútbol OR football) AND (lesión OR injury OR alineación OR lineup)'
    
    url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&pageSize=3&apiKey={api_key}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        news_summary = []
        if data.get('status') == "ok" and data.get('totalResults', 0) > 0:
            for article in data['articles']:
                news_summary.append({
                    "title": article['title'],
                    "source": article['source']['name'],
                    "url": article['url']
                })
        return news_summary
    except Exception as e:
        print(f"⚠️ Error buscando noticias para {team_name}: {e}")
        return []

def process_all_team_news():
    # 1. Cargamos los partidos que descargamos antes
    stats_path = 'Backend/data/champions_raw.json'
    if not os.path.exists(stats_path):
        print("❌ No se encontró champions_raw.json. Ejecuta primero fetcher_stats.py")
        return

    with open(stats_path, 'r', encoding='utf-8') as f:
        matches = json.load(f)

    # 2. Obtenemos equipos únicos de los próximos partidos
    upcoming_teams = set()
    for match in matches:
        if match['status'] in ['TIMED', 'SCHEDULED']:
            upcoming_teams.add(match['homeTeam']['name'])
            upcoming_teams.add(match['awayTeam']['name'])

    # 3. Buscamos noticias para cada equipo (Limitado para el piloto)
    print(f"🔍 Buscando noticias para {len(upcoming_teams)} equipos...")
    all_news = {}
    
    # Para el piloto, probaremos con los primeros 4 equipos para no agotar la API
    for team in list(upcoming_teams)[:4]:
        print(f"📰 Procesando: {team}...")
        all_news[team] = get_news_for_team(team)

    # 4. Guardamos los resultados
    os.makedirs('Backend/data', exist_ok=True)
    with open('Backend/data/news_context.json', 'w', encoding='utf-8') as f:
        json.dump(all_news, f, indent=4, ensure_ascii=False)
    
    print("✅ ¡Noticias guardadas en news_context.json!")

if __name__ == "__main__":
    process_all_team_news()