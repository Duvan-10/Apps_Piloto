"""
===========================================================
VALIDAR TORNEOS FLASHCORE
Ubicación: backend/validaciones/verificar_torneos.py

Este script se utiliza para:
- Conectar a la página principal de Flashscore (fútbol)
- Extraer y listar los nombres de los torneos principales
- Filtrar enlaces irrelevantes (ej. Resultados en vivo, Clasificación)
- Mostrar los nombres en consola
- Guardar los nombres en un archivo de texto (torneos.txt)
- Exportar los nombres a un archivo Excel (torneos.xlsx)

Se ejecuta directamente desde la raíz del proyecto:
    $ python backend/validaciones/verificar_torneos.py
===========================================================
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd

# ---------------------------------------------------------
# Función: listar_torneos
# Extrae los nombres y enlaces de los torneos desde Flashscore
# ---------------------------------------------------------
def listar_torneos():
    headers = {"User-Agent": "Mozilla/5.0"}
    url_base = "https://www.flashscore.co/futbol/"
    resp = requests.get(url_base, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    torneos = []
    enlaces = soup.select("a")
    for t in enlaces:
        texto = t.text.strip()
        href = t.get("href", "")

        # Filtrar solo enlaces de torneos principales
        if (
            texto
            and "/futbol/" in href
            and not any(x in href for x in ["clasificacion", "partidos", "resultados"])
            and len(texto) > 3  # evitar textos vacíos o irrelevantes
        ):
            torneos.append({"nombre": texto, "url": "https://www.flashscore.co" + href})

    return torneos

# ---------------------------------------------------------
# Función principal
# ---------------------------------------------------------
if __name__ == "__main__":
    torneos = listar_torneos()

    # Mostrar en consola
    print("=== Torneos principales detectados en Flashscore ===")
    for t in torneos:
        print(f"{t['nombre']} -> {t['url']}")

    # Guardar en archivo de texto
    with open("torneos.txt", "w", encoding="utf-8") as f:
        for t in torneos:
            f.write(f"{t['nombre']} -> {t['url']}\n")

    # Exportar a Excel
    df = pd.DataFrame(torneos)
    df.to_excel("torneos.xlsx", index=False)

    print("\n✅ Lista de torneos principales guardada en 'torneos.txt' y 'torneos.xlsx'")
