from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from app.agent import ReservationAgent, ReservationSession
import logging
import httpx
from app.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logging.getLogger().setLevel(logging.INFO)

# Suppress noisy loggers from dependencies
for logger_name in [
    "httpx", "uvicorn", "uvicorn.error", "uvicorn.access", "fastapi", "asyncio"
]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

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

# Создай отдельный логгер для диалогов
dialog_logger = logging.getLogger("dialog")
dialog_logger.setLevel(logging.INFO)
dialog_handler = logging.StreamHandler()
dialog_formatter = logging.Formatter('%(message)s')
dialog_handler.setFormatter(dialog_formatter)
dialog_logger.handlers = [dialog_handler]

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
    # Send initial empty message so the user (pizzeria) can speak first
    initial_response = {"content": "", "content_complete": True}
    # logging.info(f"Sending to Retell: {initial_response}")  # Убираем технический шум
    await websocket.send_json(initial_response)
    session = None
    try:
        while True:
            try:
                data = await websocket.receive_json()
                # logging.info(f"Received JSON from Retell: {data}")  # Убираем технический шум
            except Exception as e:
                logging.error(f"Error receiving JSON: {e}")
                break

            # On first message, extract reservation params and create session
            if not session:
                reservation_params = data.get("metadata") or data.get("reservation_params")
                if not reservation_params:
                    # Fallback for manual UI Retell test: use hardcoded test data
                    reservation_params = {
                        "date": "2024-03-20",
                        "time": "19:00",
                        "people": 4,
                        "name": "John Doe"
                    }
                    logging.warning("No reservation params provided by Retell. Using fallback test data.")
                session = ReservationSession(agent, reservation_params)
                sessions[call_id] = session

            # Only respond to 'response_required' interaction_type
            interaction_type = data.get("interaction_type")
            response_id = data.get("response_id")
            if interaction_type != "response_required":
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
                error_dict = {"error": "No message provided.", "content_complete": True}
                logging.error(f"Sending error to Retell: {error_dict}")
                if response_id is not None:
                    error_dict["response_id"] = response_id
                await websocket.send_json(error_dict)
                continue

            # Только диалоговые сообщения логируем явно
            dialog_logger.info(f"[User -> Agent] {message}")

            response = await session.process_message(message)

            dialog_logger.info(f"[Agent -> User] {response}")

            response_dict = {
                "content": response,
                "content_complete": True
            }
            if response_id is not None:
                response_dict["response_id"] = response_id
            await websocket.send_json(response_dict)
    except WebSocketDisconnect:
        # logging.info("WebSocket disconnected")  # Убираем технический шум
        sessions.pop(call_id, None)
    except Exception as e:
        error_dict = {"error": str(e), "content_complete": True}
        logging.error(f"WebSocket error: {e}")
        logging.error(f"Sending error to Retell: {error_dict}")
        await websocket.send_json(error_dict)
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