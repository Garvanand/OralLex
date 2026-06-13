"""
OralLex FastAPI & WebSocket Server.

Orchestrates the real-time audio capture, transcription, and streaming of
Socratic follow-up questions to the browser.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import json

from orallex.audio.whisper_asr import StreamingASR

app = FastAPI(title="OralLex - Socratic Knowledge Capture")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global ASR instance (in a real app, manage per-session or pool)
asr = StreamingASR()

@app.get("/")
async def get_ui():
    """Serve the single-file React application."""
    try:
        with open("orallex/ui/index.html", "r", encoding="utf-8") as f:
            html = f.read()
        return HTMLResponse(html)
    except Exception as e:
        logger.error(f"Failed to load UI: {e}")
        return HTMLResponse("<h1>UI not found</h1>", status_code=404)

@app.websocket("/ws/session/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    Real-time WebSocket endpoint.
    Receives audio blobs, sends transcripts and Socratic questions back.
    """
    await websocket.accept()
    logger.info(f"Session {session_id} connected.")
    
    try:
        while True:
            # Receive data from the browser (audio chunk)
            data = await websocket.receive_bytes()
            
            # 1. Process chunk through Whisper
            transcript_chunk = await asr.process_chunk(data)
            
            if transcript_chunk:
                # 2. Send transcript back to UI immediately
                payload = {
                    "type": "transcript",
                    "text": transcript_chunk
                }
                await websocket.send_text(json.dumps(payload))
                
                # 3. Trigger Pause Detection & Socratic Engine (Mocked for Hour 1)
                # In Hour 2, we will route this transcript to LangGraph.
                
    except WebSocketDisconnect:
        logger.info(f"Session {session_id} disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error in session {session_id}: {e}")
        try:
            await websocket.close()
        except:
            pass
