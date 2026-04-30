import requests
import json
import os

def get_config():
    # Buscamos el config.json en la raíz del proyecto
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def fetch_champions_data():
    config = get_config()
    # Usamos la llave de football-data.org que definiste en config.json
    api_key = config['api_keys']['football_data']
    
    # URL directa de football-data.org (CL es el código para Champions League)
    url = "https://api.football-data.org/v4/competitions/CL/matches"
    
    headers = { "X-Auth-Token": api_key }
    
    print("🛰️ Conectando con FOOTBALL-DATA.ORG...")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            # Creamos la carpeta data si no existe para evitar errores
            os.makedirs('Backend/data', exist_ok=True)
            
            # Guardamos los partidos descargados
            output_path = 'Backend/data/champions_raw.json'
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data['matches'], f, indent=4, ensure_ascii=False)
            
            print(f"✅ ¡Éxito! Se han descargado {len(data['matches'])} partidos de la Champions.")
        else:
            print(f"❌ Error {response.status_code}: Verifica tu Token de football-data.org")
            print(f"Detalle: {response.text}")

    except Exception as e:
        print(f"⚠️ Error crítico: {e}")

if __name__ == "__main__":
    fetch_champions_data()