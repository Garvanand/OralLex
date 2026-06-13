"""
OralLex Pause Detector.

Analyzes silence duration and linguistic context (trailing conjunctions) 
to determine if the expert has finished a thought and is ready for a Socratic question.
"""

import re
from loguru import logger
from orallex.models.schemas import PauseEvent

class PauseDetector:
    def __init__(self):
        self.silence_threshold_db = -40   # below this = silence
        self.thought_pause_min_ms = 3000  # minimum for a "thought" pause
        self.topic_pause_min_ms = 6000    # minimum for topic completion
        
        # Linguistic heuristic: If the transcript ends with these words,
        # the expert is mid-thought, even if there's a 3+ second pause.
        self.trailing_conjunctions = [
            "and", "so", "but", "because", "when", "if", "also", "then", "or", "like"
        ]

    def analyze_audio_buffer(
        self,
        audio_buffer: bytes,
        transcript_buffer: str,
        silence_duration_ms: int
    ) -> PauseEvent:
        """
        Analyzes recent audio for pause patterns and combines it with linguistic analysis.
        Returns the PauseEvent decision matrix.
        """
        
        if silence_duration_ms < self.thought_pause_min_ms:
            return PauseEvent(
                pause_type="natural",
                duration_ms=silence_duration_ms,
                should_ask_question=False,
                reasoning="Pause is too short to interrupt."
            )
            
        # If we have a long enough pause, check linguistics
        cleaned_transcript = re.sub(r'[^\w\s]', '', transcript_buffer.lower().strip())
        words = cleaned_transcript.split()
        
        if words and words[-1] in self.trailing_conjunctions:
            return PauseEvent(
                pause_type="mid_thought",
                duration_ms=silence_duration_ms,
                should_ask_question=False,
                reasoning=f"Expert ended with trailing conjunction '{words[-1]}'."
            )
            
        if self.detect_sentence_end(transcript_buffer):
            if silence_duration_ms >= self.topic_pause_min_ms:
                return PauseEvent(
                    pause_type="topic_completion",
                    duration_ms=silence_duration_ms,
                    should_ask_question=True,
                    reasoning="Topic completion detected (>6s silence after sentence end)."
                )
            else:
                return PauseEvent(
                    pause_type="end_of_thought",
                    duration_ms=silence_duration_ms,
                    should_ask_question=True,
                    reasoning="End of thought detected (3-6s silence after sentence end)."
                )
                
        # Fallback: long pause but no clear sentence boundary
        return PauseEvent(
            pause_type="end_of_thought",
            duration_ms=silence_duration_ms,
            should_ask_question=True,
            reasoning="Long pause without trailing conjunction detected."
        )

    def detect_sentence_end(self, transcript: str) -> bool:
        """
        Linguistic pause detection: does the transcript buffer end at a
        natural sentence boundary?
        Signals: period-like intonation patterns in transcript text.
        """
        # For transcribed text, Groq Whisper usually adds punctuation if it detects end of thought.
        if not transcript:
            return False
        return transcript.strip()[-1] in ['.', '!', '?']
