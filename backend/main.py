from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import agent_service

app = FastAPI(title="Backend TFG - Datos FAO")

# --- CONFIGURACIÓN CORS ---
# Permitir peticiones desde el frontend (React suele correr en 5173 o 3000)
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "*" # Para desarrollo
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELOS DE DATOS ---
class ChatRequest(BaseModel):
    texto: str

class ChatResponse(BaseModel):
    respuesta: str

# --- ENDPOINTS ---

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Backend funcionando 🚀"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint principal para conversar con el Agente.
    Recibe: {"texto": "mensaje usuario"}
    Devuelve: {"respuesta": "mensaje del bot..."}
    """
    try:
        print(f"📩 Recibido: {request.texto}")
        respuesta_agente = agent_service.chat_with_agent(request.texto)
        print(f"🤖 Respuesta: {respuesta_agente}")
        return ChatResponse(respuesta=respuesta_agente)
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)