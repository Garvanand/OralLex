"""
OralLex Knowledge Gap Detector & Live Graph Builder.

Analyzes transcripts in real-time, finds implicit assumptions via Claude Opus,
prioritizes gaps based on the target artifact, and generates Socratic questions.
"""

import uuid
from typing import List, Dict, Any
from loguru import logger
from langchain_anthropic import ChatAnthropic
import json

from orallex.core.config import get_settings
from orallex.models.schemas import SessionState, KnowledgeGap, Question, KnowledgeNode, KnowledgeEdge
from orallex.socratic.prompts import gap_detection_prompt, question_generation_prompt

class KnowledgeGapDetector:
    def __init__(self):
        self.settings = get_settings()
        # Claude 3 Opus is required for deep logical gap detection (curse of knowledge)
        self.llm = ChatAnthropic(
            model="claude-3-opus-20240229",
            api_key=self.settings.anthropic_api_key,
            temperature=0.2 # low temperature for analytical rigor
        )
        self.question_llm = ChatAnthropic(
            model="claude-3-haiku-20240307", # Faster for text gen
            api_key=self.settings.anthropic_api_key,
            temperature=0.7
        )

    async def analyze_transcript_chunk(
        self,
        new_text: str,
        session_state: SessionState,
        existing_gaps: List[KnowledgeGap]
    ) -> List[KnowledgeGap]:
        """
        Called on every new transcript chunk (after a pause).
        Returns NEW gaps detected in this chunk only.
        """
        if not new_text.strip():
            return []
            
        logger.info(f"Analyzing chunk for knowledge gaps: '{new_text}'")
        
        # Build context from previous chunks (last 500 words approx)
        context = " ".join([tc.text for tc in session_state.transcript_chunks[-10:]])
        
        chain = gap_detection_prompt | self.llm
        
        try:
            response = await chain.ainvoke({
                "artifact_types": ", ".join(session_state.artifact_types),
                "session_context": context,
                "new_chunk": new_text
            })
            
            # Parse Claude's JSON output
            # (In production, use PydanticOutputParser for strictness)
            raw_content = response.content
            start_idx = raw_content.find('[')
            end_idx = raw_content.rfind(']') + 1
            if start_idx != -1 and end_idx != 0:
                gap_data = json.loads(raw_content[start_idx:end_idx])
            else:
                return []
                
            new_gaps = []
            existing_phrases = {g.triggering_phrase.lower() for g in existing_gaps}
            
            for g_dict in gap_data:
                phrase = g_dict.get("triggering_phrase", "")
                if phrase.lower() in existing_phrases:
                    continue # Deduplicate
                    
                gap = KnowledgeGap(
                    gap_id=str(uuid.uuid4()),
                    session_id=session_state.session_id,
                    gap_type=g_dict.get("gap_type", "implicit_assumption"),
                    triggering_phrase=phrase,
                    triggering_timestamp_ms=0, # Simplified for MVP
                    gap_description=g_dict.get("gap_description", ""),
                    importance_score=float(g_dict.get("importance_score", 0.5)),
                    target_artifact_types=session_state.artifact_types
                )
                new_gaps.append(gap)
                
            return new_gaps
            
        except Exception as e:
            logger.error(f"Gap detection failed: {e}")
            return []

    async def prioritize_gaps(
        self,
        gaps: List[KnowledgeGap],
        topic: str,
        artifact_types: List[str]
    ) -> List[KnowledgeGap]:
        """
        Rank gaps by importance for the target artifact type.
        """
        if not gaps:
            return []
            
        # Sorting logic:
        # 1. Base importance_score assigned by Claude
        # 2. Boost based on Artifact Type alignment
        def score_gap(gap: KnowledgeGap) -> float:
            score = gap.importance_score
            if "SOP" in artifact_types and gap.gap_type == "undocumented_prerequisite":
                score += 0.3
            elif "FAQ" in artifact_types and gap.gap_type == "missing_edge_case":
                score += 0.3
            elif "Decision Tree" in artifact_types and gap.gap_type == "unexplained_causality":
                score += 0.3
            return min(1.0, score)
            
        return sorted(gaps, key=score_gap, reverse=True)

    async def generate_question(
        self,
        gap: KnowledgeGap,
        conversation_context: str,
        questions_already_asked: List[str]
    ) -> Question:
        """
        Generate a specific, natural-sounding follow-up question < 25 words.
        """
        chain = question_generation_prompt | self.question_llm
        
        try:
            response = await chain.ainvoke({
                "gap_type": gap.gap_type,
                "triggering_phrase": gap.triggering_phrase,
                "gap_description": gap.gap_description
            })
            
            question_text = response.content.strip().replace('"', '')
            
            # Hard cutoff if Claude ignores the 25 word limit
            words = question_text.split()
            if len(words) > 25:
                question_text = " ".join(words[:25]) + "?"
                
            return Question(
                question_id=str(uuid.uuid4()),
                text=question_text,
                type=gap.gap_type,
                status="pending"
            )
        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            return Question(
                question_id=str(uuid.uuid4()),
                text=f"Could you elaborate more on what you meant by '{gap.triggering_phrase}'?",
                type="fallback",
                status="pending"
            )

    async def update_knowledge_graph(self, session_state: SessionState) -> None:
        """
        Live concept map builder. Analyzes the full transcript and updates coverage scores.
        """
        # MVP Mock implementation: Updates coverage score linearly with transcript length
        # In reality, this requires a separate LangChain entity extraction pipeline
        words = len(session_state.full_transcript.split())
        
        # Assume 1000 words = 100% coverage for a single topic MVP
        coverage = min(1.0, words / 1000.0)
        session_state.coverage_score = coverage
        
        logger.info(f"Updated live Knowledge Graph. Topic coverage: {coverage*100:.1f}%")
