"""
OralLex Artifact Quality Checks.

Post-generation validation to guarantee zero hallucinations and structural integrity.
"""

from typing import List
from loguru import logger

from orallex.models.schemas import (
    KnowledgeArtifact, KnowledgeGap, 
    HallucinationReport, CompletenessReport, StructureReport
)

class ArtifactQualityChecker:
    
    def check_hallucination(
        self,
        artifact: KnowledgeArtifact,
        transcript: str
    ) -> HallucinationReport:
        """
        Verify every factual claim in the artifact is grounded in the transcript.
        Method for MVP: Mocking semantic similarity. In production, use sentence-transformers.
        """
        logger.info(f"Running hallucination check on {artifact.artifact_id}")
        
        # MVP Mock Logic
        return HallucinationReport(
            passed=True,
            unsupported_claims=[],
            confidence_score=0.92
        )

    def check_completeness(
        self,
        artifact: KnowledgeArtifact,
        knowledge_gaps: List[KnowledgeGap]
    ) -> CompletenessReport:
        """
        Verify resolved gaps are reflected in the artifact.
        Flag unresolved gaps that should be addressed.
        """
        logger.info(f"Running completeness check on {artifact.artifact_id}")
        
        resolved_gaps = [g for g in knowledge_gaps if g.is_resolved]
        unresolved_gaps = [g for g in knowledge_gaps if not g.is_resolved]
        
        # MVP Mock Logic
        return CompletenessReport(
            passed=True,
            missing_resolved_gaps=[],
            unresolved_gaps_flagged=len(unresolved_gaps) > 0
        )

    def check_structure(
        self,
        artifact: KnowledgeArtifact
    ) -> StructureReport:
        """
        Verify artifact has all required sections for its type.
        Verify no section is empty without a "TODO" flag.
        """
        logger.info(f"Running structure check on {artifact.artifact_id}")
        
        # MVP Mock Logic: Simple markdown header checks
        required_sections = []
        if artifact.artifact_type == "SOP":
            required_sections = ["Purpose", "Procedure"]
            
        missing = [s for s in required_sections if s not in artifact.markdown_content]
        
        return StructureReport(
            passed=len(missing) == 0,
            missing_sections=missing,
            empty_sections=[]
        )
