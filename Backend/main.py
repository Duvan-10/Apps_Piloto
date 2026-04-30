import subprocess
import os

def actualizar_todo():
    # Obtenemos la ruta donde está este archivo (Backend/)
    base_path = os.path.dirname(__file__)
    
    # Rutas relativas a los procesadores
    stats = os.path.join(base_path, "processors", "fetcher_stats.py")
    news = os.path.join(base_path, "processors", "fetcher_news.py")
    calc = os.path.join(base_path, "processors", "calculator.py")

    print("🔄 Iniciando actualización completa de datos...")
    
    subprocess.run(["python", stats])
    subprocess.run(["python", news])
    subprocess.run(["python", calc])
    
    print("✨ ¡Proceso terminado! Datos listos para la API.")

if __name__ == "__main__":
    actualizar_todo()