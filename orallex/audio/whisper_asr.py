"""
OralLex Groq Whisper ASR Integration.

Handles streaming transcription of audio chunks sent over WebSockets.
"""

import os
import io
import asyncio
from loguru import logger
from groq import AsyncGroq

from orallex.core.config import get_settings

class StreamingASR:
    """Manages audio buffer and Whisper API transcription via Groq."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncGroq(api_key=self.settings.groq_api_key)
        self.buffer = bytearray()
        
    async def process_chunk(self, audio_chunk: bytes) -> str:
        """
        Processes a raw webm/ogg chunk from the browser MediaRecorder.
        For true streaming, we accumulate chunks until a certain size or pause,
        then send to Whisper. For MVP, we'll transcribe on a sliding window or
        upon explicit flush requests.
        """
        # In a real production system, handling WebM chunks mid-stream requires 
        # either a media container parser or continuous ffmpeg piping.
        # For this MVP, we assume the chunk is a valid, transcribeable audio file 
        # (e.g. the browser sends discrete blobs).
        
        if not audio_chunk:
            return ""
            
        try:
            # Wrap the raw bytes in a file-like object for the API
            audio_file = io.BytesIO(audio_chunk)
            audio_file.name = "chunk.webm"
            
            # Use Whisper large-v3 via Groq for ultra-low latency
            transcription = await self.client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                prompt="Socratic technical interview session.",
                response_format="text",
                language="en"
            )
            
            text = str(transcription).strip()
            logger.debug(f"ASR Transcript: {text}")
            return text
            
        except Exception as e:
            logger.error(f"Whisper ASR error: {e}")
            return ""
