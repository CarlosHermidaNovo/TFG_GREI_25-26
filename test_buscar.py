"""Test directo de la herramienta buscar_y_graficar"""
import sys
sys.path.insert(0, 'backend')

from agent import buscar_y_graficar

print("=" * 60)
print("TEST 1: Buscar PIB")
print("=" * 60)
resultado = buscar_y_graficar.invoke({"query": "pib"})
print(f"Resultado: {resultado}")

print("\n" + "=" * 60)
print("TEST 2: Buscar población urbana")
print("=" * 60)
resultado = buscar_y_graficar.invoke({"query": "población urbana"})
print(f"Resultado: {resultado}")

print("\n" + "=" * 60)
print("TEST 3: Buscar obesidad")
print("=" * 60)
resultado = buscar_y_graficar.invoke({"query": "obesidad"})
print(f"Resultado: {resultado}")
