"""
OralLex Real-Time Session Server.

FastAPI WebSocket orchestrator implementing the Session State Machine,
Pause Detection, and streaming audio processing.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import json
import time
from datetime import datetime

from orallex.session.asr_client import StreamingASR
from orallex.session.pause_detector import PauseDetector
from orallex.models.schemas import SessionState, TranscriptChunk

app = FastAPI(title="OralLex - Real-Time Session Engine")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory Redis mock for MVP
active_sessions = {}

asr_client = StreamingASR()
pause_detector = PauseDetector()

@app.websocket("/ws/session/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    logger.info(f"Session {session_id} connected.")
    
    # Initialize State Machine
    state = SessionState(
        session_id=session_id,
        expert_name="Unknown Expert",
        topic="General",
        artifact_types=["SOP"],
        status="active"
    )
    active_sessions[session_id] = state
    
    last_audio_receive_time = time.time()
    
    try:
        while True:
            # 1. Receive data (Simulating AudioChunk from client)
            data = await websocket.receive_bytes()
            current_time = time.time()
            
            # Calculate silence gap since last chunk
            silence_ms = int((current_time - last_audio_receive_time) * 1000)
            last_audio_receive_time = current_time
            
            # 2. Process chunk through Whisper
            # Pass recent context for continuity
            recent_context = " ".join([tc.text for tc in state.transcript_chunks[-3:]])
            transcription_chunk = await asr_client.transcribe_chunk(data, session_context=recent_context)
            
            if transcription_chunk.text:
                # Update state
                new_chunk = TranscriptChunk(
                    sequence=len(state.transcript_chunks),
                    text=transcription_chunk.text,
                    timestamp=datetime.utcnow()
                )
                state.transcript_chunks.append(new_chunk)
                state.full_transcript += " " + transcription_chunk.text
                
                # Send transcript back to UI
                await websocket.send_text(json.dumps({
                    "type": "transcript",
                    "text": transcription_chunk.text,
                    "is_final": True,
                    "confidence": transcription_chunk.confidence,
                    "timestamp_ms": int(current_time * 1000)
                }))
                
                # 3. Analyze for Pause Event
                pause_event = pause_detector.analyze_audio_buffer(
                    audio_buffer=data,
                    transcript_buffer=state.full_transcript,
                    silence_duration_ms=silence_ms
                )
                
                if pause_event.should_ask_question:
                    logger.info(f"Socratic Question Triggered! Reason: {pause_event.reasoning}")
                    # Hour 2: Call Socratic Engine LangGraph here
                    # Mocking response for now
                    mock_question = {
                        "type": "question",
                        "question_text": "You mentioned this process usually works. What are the specific conditions where it fails?",
                        "question_type": "edge_case",
                        "triggered_by": transcription_chunk.text,
                        "priority": 1
                    }
                    await websocket.send_text(json.dumps(mock_question))
                
    except WebSocketDisconnect:
        logger.info(f"Session {session_id} disconnected.")
        state.status = "paused"
    except Exception as e:
        logger.error(f"WebSocket error in session {session_id}: {e}")
        try:
            await websocket.close()
        except:
            pass
