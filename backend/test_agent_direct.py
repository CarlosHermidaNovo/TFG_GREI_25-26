"""Test directo del agente para debugging"""
from agent import chat_with_agent

print("=" * 60)
print("TEST: Llamada directa al agente")
print("=" * 60)

respuesta = chat_with_agent("Quiero ver el pib")

print("\n" + "=" * 60)
print("RESPUESTA FINAL:")
print("=" * 60)
print(respuesta)
