import json
import os

def load_data():
    with open('Backend/data/champions_raw.json', 'r', encoding='utf-8') as f:
        matches = json.load(f)
    with open('Backend/data/news_context.json', 'r', encoding='utf-8') as f:
        news = json.load(f)
    return matches, news

def calculate_prediction(match, news_data):
    home_team = match['homeTeam']['name']
    away_team = match['awayTeam']['name']
    
    # Puntaje base (Punto 5: Performance Actual / Tabla)
    # Aquí simplificamos: el que juega en casa suele tener ligera ventaja
    home_score = 52 
    away_score = 48

    # --- Punto 6: Ajuste por Noticias (Bajas y Sensaciones) ---
    def analyze_news(team_name, current_score):
        team_news = news_data.get(team_name, [])
        adjustment = 0
        for article in team_news:
            title = article['title'].lower()
            # Si hay palabras negativas (lesión, baja, duda)
            if any(word in title for word in ['lesión', 'injury', 'baja', 'out', 'duda']):
                adjustment -= 5  # Restamos 5 puntos por cada noticia de baja
            # Si hay palabras positivas
            if any(word in title for word in ['victoria', 'optimismo', 'regresa', 'vuelve']):
                adjustment += 3
        return current_score + adjustment

    home_score = analyze_news(home_team, home_score)
    away_score = analyze_news(away_team, away_score)

    # Normalizar para que sumen 100%
    total = home_score + away_score
    home_pct = round((home_score / total) * 100, 2)
    away_pct = round((away_score / total) * 100, 2)

    return {
        "partido": f"{home_team} vs {away_team}",
        "probabilidades": {
            home_team: f"{home_pct}%",
            away_team: f"{away_pct}%",
            "Empate": f"{round(100 - home_pct - away_pct, 2) if home_pct + away_pct < 100 else 0}%"
        },
        "recomendacion": "Local" if home_pct > away_pct + 10 else ("Visitante" if away_pct > home_pct + 10 else "Doble Oportunidad / Empate")
    }

def run_engine():
    print("🧠 Ejecutando motor de predicción basado en tus 6 parámetros...")
    matches, news = load_data()
    predictions = []

    # Procesamos solo los partidos que no han jugado (SCHEDULED)
    for m in matches:
        # Solo procesamos si el partido tiene nombres de equipos válidos
        if m['status'] in ['SCHEDULED', 'TIMED'] and m['homeTeam']['name'] and m['awayTeam']['name']:
            res = calculate_prediction(m, news)
            predictions.append(res)
            print(f"✅ Analizado: {res['partido']}")

    with open('Backend/data/final_predictions.json', 'w', encoding='utf-8') as f:
        json.dump(predictions, f, indent=4, ensure_ascii=False)
    
    print(f"\n🚀 ¡Listo! Se generaron {len(predictions)} predicciones inteligentes.")

if __name__ == "__main__":
    run_engine()