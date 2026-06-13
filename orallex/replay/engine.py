"""
OralLex Session Replay & Annotation Engine.

Handles post-session expert annotations, transcript modifications,
and the creation of Expansion Sessions for deep dives.
"""

import uuid
from typing import List
from loguru import logger
from langchain_anthropic import ChatAnthropic

from orallex.core.config import get_settings
from orallex.models.schemas import Annotation, KnowledgeArtifact, ExpansionSession, SessionState
from orallex.artifacts.generator import ArtifactGenerator

class AnnotationEngine:
    """Processes expert annotations to rebuild transcripts and artifacts."""
    
    def __init__(self):
        self.settings = get_settings()
        self.artifact_gen = ArtifactGenerator()
        self.llm = ChatAnthropic(
            model="claude-3-haiku-20240307",
            api_key=self.settings.anthropic_api_key,
            temperature=0.7
        )

    async def regenerate_from_annotations(
        self,
        session: SessionState,
        annotation_set: List[Annotation]
    ) -> List[KnowledgeArtifact]:
        """
        Apply annotations to transcript before re-generation.
        """
        logger.info(f"Regenerating artifacts for session {session.session_id} with {len(annotation_set)} annotations.")
        
        modified_transcript = session.full_transcript
        
        # Sort annotations by end position (descending) to avoid offset shifting when mutating string
        sorted_annos = sorted(annotation_set, key=lambda x: getattr(x, 'transcript_end_ms', 0), reverse=True)
        
        for anno in sorted_annos:
            text = anno.highlighted_text
            
            if anno.annotation_type in ["delete", "private"]:
                # Simply excise the text
                modified_transcript = modified_transcript.replace(text, f"[REDACTED: {anno.annotation_type}]")
                logger.debug(f"Applied DELETE/PRIVATE annotation to: '{text[:20]}...'")
                
            elif anno.annotation_type == "add_context":
                # Inject added context
                injection = f" {text} [EXPERT NOTE: {anno.added_context}] "
                modified_transcript = modified_transcript.replace(text, injection)
                logger.debug(f"Applied ADD_CONTEXT annotation.")
                
            elif anno.annotation_type == "important":
                # Boost importance for the artifact generation prompt
                injection = f" **[CRITICAL: {text}]** "
                modified_transcript = modified_transcript.replace(text, injection)
                
            elif anno.annotation_type == "expand":
                # Trigger expansion session logic (handled separately, but we note it)
                pass

        # Temporarily mutate the session state for the generator
        session.full_transcript = modified_transcript
        
        # Re-run generator
        return await self.artifact_gen.generate_all_requested_artifacts(session, session.artifact_types)


    async def create_expansion_session(
        self,
        parent_session_id: str,
        expand_annotation: Annotation
    ) -> ExpansionSession:
        """
        Generate a mini-session (15-20 min) focused on the flagged section.
        Pre-loads 5 targeted questions based on the unexplored area.
        """
        logger.info(f"Creating expansion session from parent {parent_session_id} based on expand annotation.")
        
        prompt = f"""
        The expert highlighted the following text from an interview and marked it for EXPANSION:
        "{expand_annotation.highlighted_text}"
        
        Generate exactly 5 targeted, Socratic follow-up questions to explore this specific area deeply.
        Output them as a simple newline separated list.
        """
        
        response = await self.llm.ainvoke([("human", prompt)])
        questions = [q.strip() for q in response.content.strip().split("\n") if q.strip()]
        
        return ExpansionSession(
            session_id=str(uuid.uuid4()),
            parent_session_id=parent_session_id,
            focus_topic=f"Deep Dive: {expand_annotation.highlighted_text[:30]}...",
            preloaded_questions=questions[:5],
            status="pending"
        )
