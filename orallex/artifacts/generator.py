"""
OralLex Multi-Artifact Generation Orchestrator.

Generates multiple requested artifacts in parallel, applies quality checks,
and runs semantic deduplication.
"""

import asyncio
import uuid
from datetime import datetime
from typing import List
from loguru import logger
from langchain_anthropic import ChatAnthropic

from orallex.core.config import get_settings
from orallex.models.schemas import SessionState, KnowledgeArtifact
from orallex.artifacts.prompts import get_artifact_prompt
from orallex.artifacts.quality import ArtifactQualityChecker
from orallex.artifacts.dedup import check_existing_knowledge

class ArtifactGenerator:
    def __init__(self):
        self.settings = get_settings()
        self.llm = ChatAnthropic(
            model="claude-3-opus-20240229", # Opus for heavy generation
            api_key=self.settings.anthropic_api_key,
            temperature=0.3
        )
        self.quality_checker = ArtifactQualityChecker()

    async def _generate_single_artifact(self, session: SessionState, artifact_type: str) -> KnowledgeArtifact:
        """Core generation logic for a single type."""
        logger.info(f"Generating {artifact_type} artifact for session {session.session_id}")
        
        prompt = get_artifact_prompt(artifact_type)
        chain = prompt | self.llm
        
        # Serialize resolved gaps for the prompt
        resolved_gaps = [g for g in session.questions_asked if g.status == "answered"]
        gaps_text = "\n".join([f"- Gap: {g.text} | Answer: {getattr(g, 'expert_response', 'N/A')}" for g in resolved_gaps])
        
        try:
            response = await chain.ainvoke({
                "artifact_type": artifact_type,
                "transcript": session.full_transcript,
                "resolved_gaps": gaps_text or "No specific resolved gaps."
            })
            
            markdown_content = response.content.strip()
            
            artifact = KnowledgeArtifact(
                artifact_id=str(uuid.uuid4()),
                session_id=session.session_id,
                artifact_type=artifact_type,
                title=f"{session.topic} - {artifact_type}",
                markdown_content=markdown_content,
                generated_at=datetime.utcnow(),
                status="draft"
            )
            
            # Run Quality Checks
            hallucination_rep = self.quality_checker.check_hallucination(artifact, session.full_transcript)
            if not hallucination_rep.passed:
                logger.warning(f"Hallucination check failed for {artifact.artifact_id}")
                
            return artifact
            
        except Exception as e:
            logger.error(f"Failed to generate {artifact_type}: {e}")
            raise e

    async def generate_all_requested_artifacts(
        self,
        session: SessionState,
        requested_types: List[str]
    ) -> List[KnowledgeArtifact]:
        """
        Generate artifacts in parallel.
        """
        logger.info(f"Starting parallel generation of {len(requested_types)} artifacts.")
        
        tasks = [self._generate_single_artifact(session, a_type) for a_type in requested_types]
        artifacts = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_artifacts = []
        for a in artifacts:
            if isinstance(a, Exception):
                logger.error(f"Task failed: {a}")
            else:
                # Deduplication Check
                dedup_result = await check_existing_knowledge(a, "agentos_org")
                if dedup_result.action == "create_new" or dedup_result.action == "auto_link":
                    valid_artifacts.append(a)
                else:
                    logger.info(f"Artifact {a.artifact_id} skipped due to deduplication (Merge required).")
                    
        return valid_artifacts

    # Export Stubs
    async def export_to_notion(self, artifact: KnowledgeArtifact, notion_db_id: str):
        pass

    async def export_to_confluence(self, artifact: KnowledgeArtifact, space_key: str):
        pass
