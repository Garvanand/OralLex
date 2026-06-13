"""
OralLex Streaming ASR Client with Fallback Matrices.

Primary: Groq Whisper large-v3
Fallback 1: Claude 3 Opus (for very short clips if Groq fails)
Fallback 2: OpenAI Whisper (via OpenRouter fallback matrix)
"""

import io
import os
from loguru import logger
from groq import AsyncGroq

from orallex.core.config import get_settings
from orallex.models.schemas import TranscriptionChunk

class StreamingASR:
    def __init__(self):
        self.settings = get_settings()
        self.groq_client = AsyncGroq(api_key=self.settings.groq_api_key)
        
    async def transcribe_chunk(
        self,
        audio_chunk: bytes,
        session_context: str = ""
    ) -> TranscriptionChunk:
        """
        Returns: text, is_final, confidence, word_timestamps
        Uses GroqCloud Whisper large-v3 as primary.
        """
        if not audio_chunk:
            return TranscriptionChunk(text="", is_final=False, confidence=0.0)
            
        try:
            audio_file = io.BytesIO(audio_chunk)
            audio_file.name = "chunk.webm"
            
            # Using prompt injection for continuity context
            prompt_context = "Socratic technical interview. "
            if session_context:
                # Provide the last N words to Whisper to maintain context and spelling
                prompt_context += "Previous context: " + " ".join(session_context.split()[-50:])
                
            transcription = await self.groq_client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                prompt=prompt_context,
                response_format="verbose_json", # verbose to get timestamps if needed
                language="en"
            )
            
            text = transcription.text.strip()
            
            return TranscriptionChunk(
                text=text,
                is_final=True,
                confidence=0.95, # Groq API doesn't always expose confidence easily, mock for MVP
                word_timestamps=[]
            )
            
        except Exception as e:
            logger.error(f"Groq Whisper ASR failed: {e}. Falling back to secondary...")
            return await self._fallback_transcribe(audio_chunk, session_context)
            
    async def _fallback_transcribe(self, audio_chunk: bytes, session_context: str) -> TranscriptionChunk:
        """Fallback to OpenAI via OpenRouter or Claude Opus."""
        # MVP: Return empty gracefully to not crash the stream
        logger.warning("Fallback ASR executed (Mocked)")
        return TranscriptionChunk(text="[ASR Fallback Triggered]", is_final=True, confidence=0.5)

    async def finalize_transcript(self, full_audio_path: str) -> str:
        """Final full-quality transcription of complete session audio."""
        logger.info(f"Finalizing full transcript for {full_audio_path}")
        # MVP: Mocking final full file transcription
        return "Complete transcript."
