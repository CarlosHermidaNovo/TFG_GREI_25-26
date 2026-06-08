import sys
import os

# Add the current directory to sys.path so we can import agent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent import listar_metricas_disponibles

try:
    print("--- Tool Output Start ---")
    result = listar_metricas_disponibles.invoke({})
    with open("debug_output.txt", "w", encoding="utf-8") as f:
        f.write(result)
    print("--- Tool Output Written to debug_output.txt ---")
except Exception as e:
    print(f"Error: {e}")
