"""
===========================================================
SCRIPTING AÑADIR TORNEOS
Ubicación: backend/calendario/Scripting_añadir_torneos.py

Este script se utiliza para añadir torneos actuales a la base de datos
de manera automática, usando las funciones definidas en gestor_torneos.py.

Flujo:
- Importa la función add_tournament_by_name desde gestor_torneos
- Añade torneos vigentes (ej. Premier League 2026, LaLiga EA Sports 2026)
- Sincroniza automáticamente equipos y partidos asociados

Se ejecuta directamente desde la raíz del proyecto:
    $ python backend/calendario/Scripting_añadir_torneos.py
===========================================================
"""
import sys
import os

# Añadir la raíz del proyecto al sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Importar función principal desde gestor_torneos
from backend.calendario.gestor_torneos import add_tournament_by_name

# ---------------------------------------------------------
# Añadir torneos actuales
# ---------------------------------------------------------
#
# Ejemplo Añadir Torneo
#add_tournament_by_name("name_torneo")


add_tournament_by_name("LaLiga EA Sports")

