from langchain_ollama import ChatOllama
from langchain_core.tools import tool

@tool
def sumar(a: int, b: int) -> int:
    """Suma dos números."""
    return a + b

llm = ChatOllama(model="qwen2.5", temperature=0)

llm_with_tools = llm.bind_tools([sumar])

print("Probando tool call simple...")
try:
    response = llm_with_tools.invoke("Cuanto es 2 + 2?")
    print(f"Tipo respuesta: {type(response)}")
    print(f"Contenido: {response.content}")
    print(f"Tool Calls: {response.tool_calls}")
    print(f"Resultado: {response.tool_calls[0].result}")
except Exception as e:
    print(f"Error: {e}")
