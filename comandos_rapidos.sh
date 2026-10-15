#!/bin/bash
# Comandos rápidos de Pulso.
#
# TODOS los comandos de este fichero se ejecutaron y funcionaron antes de
# incluirlos (12 de octubre de 2026, Windows 11, Python 3.14.7).
#
# Ejecutar desde la raíz del proyecto.
#
# Antes de usarlos, definir la clave (la autorización es obligatoria):
#   export NOOSFERA_API_KEY=noosfera_local_prueba_2026
#   export PYTHONPATH=$PWD
#   export NOOSFERA_HOME=$PWD

echo "Pulso — comandos rápidos"
echo "========================"
echo ""
echo "Los comandos están comentados para poder copiarlos uno a uno."
echo ""
# 1. Ver el estado del sistema
#    python -m noosfera_project.cli estado

# 2. Ejecutar un ciclo completo (dashboard + informe + PDF)
#    python -m noosfera_project.cli ciclo

# 3. Ver todos los comandos de la CLI
#    python -m noosfera_project.cli --help

# 4. Verificar todo el proyecto
#    python verificar_pulso.py

# 5. Comprobar la salud del sistema
#    python noosfera_project/tests/health_check.py

# 6. Comprobar la estructura del árbol
#    python noosfera_project/tests/estructura_suite.py

# 7. Batería funcional completa (levanta un servidor de verdad)
#    python noosfera_project/tests/bateria_funcional_parte3.py

# 8. Todas las pruebas con pytest
#    python -m pytest noosfera_project/tests/ -q

# 9. Clasificar un texto por tema
#    python -c "from noosfera_project.procesamiento.clasificador_tematico import clasificar; print(clasificar('bitcoin sube 10%'))"

# 10. Detectar el idioma de un texto
#    python -c "from noosfera_project.procesamiento.idioma import detectar_idioma; print(detectar_idioma('El bitcoin se hunde'))"

# 11. Puntuar un evento
#    python -c "from noosfera_project.procesamiento.scoring import calcular_score; s=calcular_score({'titulo':'Crisis economica','categorias':'economia','publicado':'2026-10-01T00:00:00+00:00','texto':'inflacion'}); print(s.puntuacion, s.nivel)"

# 12. Levantar el servidor (Windows)
#    iniciar_noosfera.bat

# 13. Levantar el servidor (Linux/macOS)
#    ./iniciar_noosfera.sh

# 14. Levantar el servidor a mano
#    python noosfera.py --server 8080
