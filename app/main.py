from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from app.agent import ReservationAgent, ReservationSession
import logging
import httpx
from app.config import get_settings

app = FastAPI(
    title="Voice Reserve AI",
    description="AI-powered restaurant reservation system",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the agent
agent = ReservationAgent()
sessions: Dict[str, ReservationSession] = {}

class ChatRequest(BaseModel):
    message: str
    chat_history: Optional[List[Dict[str, str]]] = None

class ChatResponse(BaseModel):
    response: str

class ReservationRequest(BaseModel):
    date: str
    time: str
    people: int
    name: str
    phone_number: str  # номер пиццерии

async def initiate_retell_call(
    api_key: str,
    phone_number: str,
    llm_url: str,
    metadata: dict = None
):
    url = "https://api.retellai.com/v1/call"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "phone_number": phone_number,
        "custom_llm_url": llm_url,
        "metadata": metadata or {}
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

settings = get_settings()

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Voice Reserve AI",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0"
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message and return the agent's response."""
    try:
        response = await agent.process_message(
            message=request.message,
            chat_history=request.chat_history
        )
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/llm-websocket/{call_id}")
async def llm_websocket(websocket: WebSocket, call_id: str):
    """
    WebSocket endpoint for real-time communication with the LangChain agent.
    Receives messages from Retell, processes them with the agent, and sends responses back in the expected format.
    """
    await websocket.accept()
    session = None
    try:
        while True:
            try:
                data = await websocket.receive_json()
                logging.info(f"Received JSON from Retell: {data}")
            except Exception as e:
                logging.error(f"Error receiving JSON: {e}")
                break

            # On first message, extract reservation params and create session
            if not session:
                reservation_params = data.get("metadata") or data.get("reservation_params")
                if reservation_params:
                    session = ReservationSession(agent, reservation_params)
                    sessions[call_id] = session
                else:
                    await websocket.send_json({"error": "No reservation params provided.", "content_complete": True})
                    continue

            # Extract user message from transcript
            message = None
            transcript = data.get("transcript")
            if transcript and isinstance(transcript, list) and len(transcript) > 0:
                for entry in reversed(transcript):
                    if entry.get("role") == "user":
                        message = entry.get("content")
                        break

            if not message:
                await websocket.send_json({"error": "No message provided.", "content_complete": True})
                continue

            response = await session.process_message(message)
            logging.info(f"Sending to Retell: {response}")

            await websocket.send_json({
                "response": response,
                "content_complete": True
            })
    except WebSocketDisconnect:
        logging.info("WebSocket disconnected")
        sessions.pop(call_id, None)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        await websocket.send_json({"error": str(e), "content_complete": True})
        await websocket.close()
        sessions.pop(call_id, None)

@app.post("/call-reserve")
async def call_reserve(request: ReservationRequest):
    # Сформировать публичный LLM endpoint (ngrok url)
    llm_url = f"{settings.host}/llm-websocket/{{call_id}}"  # Заменить на твой публичный адрес!
    metadata = {
        "date": request.date,
        "time": request.time,
        "people": request.people,
        "name": request.name
    }
    try:
        result = await initiate_retell_call(
            api_key=settings.retell_api_key,
            phone_number=request.phone_number,
            llm_url=llm_url,
            metadata=metadata
        )
        return {"status": "initiated", "retell_response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 