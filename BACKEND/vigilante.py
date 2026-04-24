import json
from urllib.parse import quote_plus
from urllib.request import urlopen

# Reemplaza con tu NewsAPI Key real
NEWS_API_KEY = 'c3ce6259bb39400a912615fb57233328'

def analizar_sentimiento_equipo(nombre_equipo):
    # Palabras que indican un buen momento
    positivas = ['win', 'victory', 'confident', 'ready', 'fit', 'boost', 'star', 'strong', 'signing']
    # Palabras que indican problemas
    negativas = ['injury', 'out', 'miss', 'doubt', 'defeat', 'loss', 'crisis', 'bad', 'problem', 'ban']

    query = quote_plus(f"{nombre_equipo} football")
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    
    try:
        with urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        articulos = data.get('articles', [])[:5] # Analizamos 5 titulares
        
        if not articulos:
            return 0.0
        
        puntaje = 0.0
        for art in articulos:
            titulo = art['title'].lower()
            # Si el título tiene palabras buenas, suma. Si tiene malas, resta.
            for p in positivas:
                if p in titulo: puntaje += 0.25
            for n in negativas:
                if n in titulo: puntaje -= 0.25
        
        return round(puntaje, 2)
    except Exception as e:
        print(f"Error en vigilante para {nombre_equipo}: {e}")
        return 0.0