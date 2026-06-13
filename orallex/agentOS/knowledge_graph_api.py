"""
OralLex AgentOS API.

The "Expertise Layer" of AgentOS. Exposes captured tacit knowledge
to all other agents via REST endpoints and RAG.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from loguru import logger
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

from orallex.core.config import get_settings
from orallex.models.schemas import KnowledgeArtifact

router = APIRouter(prefix="/v1/agentOS/knowledge", tags=["AgentOS Shared Knowledge"])

# ==============================================================================
# SCHEMAS
# ==============================================================================

class SearchQuery(BaseModel):
    org_id: str
    query: str
    artifact_type: Optional[str] = None
    domain: Optional[str] = None
    top_k: int = 5

class ArtifactSummary(BaseModel):
    artifact_id: str
    title: str
    type: str
    similarity_score: float
    snippet: str

class RAGQuery(BaseModel):
    org_id: str
    question: str
    context: Optional[str] = None
    requesting_agent: str

class RAGAnswer(BaseModel):
    answer: str
    source_artifact_id: str
    source_quote: str
    confidence: float

class SessionSuggestionRequest(BaseModel):
    org_id: str
    knowledge_gap_description: str

class SessionSuggestion(BaseModel):
    suggested_topic: str
    estimated_duration_mins: int
    suggested_expert: str

class CoverageMap(BaseModel):
    org_id: str
    domains_covered: List[str]
    coverage_score: float
    sparse_domains: List[str]

# ==============================================================================
# RAG ENGINE
# ==============================================================================

class KnowledgeRAG:
    """Answers questions based on OralLex artifacts."""
    def __init__(self):
        self.settings = get_settings()
        self.llm = ChatAnthropic(
            model="claude-3-haiku-20240307",
            api_key=self.settings.anthropic_api_key,
            temperature=0.0
        )
        # Mock ChromaDB connection for MVP
        
    async def answer_from_artifacts(self, query: RAGQuery) -> RAGAnswer:
        logger.info(f"Agent '{query.requesting_agent}' requested RAG for '{query.question}'")
        
        # 1. Embed question
        # 2. Query ChromaDB for org_id
        # 3. Retrieve chunks
        # MOCK IMPLEMENTATION
        mock_retrieved_text = "Deployments usually fail if the cache isn't cleared first."
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are the OralLex RAG agent. Answer the question based ONLY on the provided context. You must quote the source."),
            ("human", f"Context: {mock_retrieved_text}\n\nQuestion: {query.question}")
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({})
        
        return RAGAnswer(
            answer=response.content,
            source_artifact_id="art_123",
            source_quote="Deployments usually fail if the cache isn't cleared first.",
            confidence=0.85
        )

rag_engine = KnowledgeRAG()

# ==============================================================================
# ENDPOINTS
# ==============================================================================

@router.post("/search", response_model=List[ArtifactSummary])
async def search_knowledge(query: SearchQuery):
    """
    Search artifacts by semantic similarity.
    Used by: ThreadSmith (support SOPs), SynthSenior (design docs)
    """
    logger.info(f"Searching knowledge base for org {query.org_id} (Query: {query.query})")
    # Mock return
    return [
        ArtifactSummary(
            artifact_id="art_123",
            title="Deployment Failure Troubleshooting",
            type="TROUBLESHOOTING_GUIDE",
            similarity_score=0.92,
            snippet="If the pod fails to start, check the Redis cache connection..."
        )
    ]

@router.get("/artifact/{artifact_id}", response_model=KnowledgeArtifact)
async def get_artifact(artifact_id: str):
    """Retrieve full artifact content."""
    # Mock DB fetch
    raise HTTPException(status_code=404, detail="Artifact not found (Mock)")

@router.post("/query_answer", response_model=RAGAnswer)
async def query_answer(query: RAGQuery):
    """
    RAG over artifacts to answer specific questions.
    Used by: ThreadSmith (answering customer questions based on internal FAQs)
    """
    return await rag_engine.answer_from_artifacts(query)

@router.post("/suggest_session", response_model=SessionSuggestion)
async def suggest_session(req: SessionSuggestionRequest):
    """
    Suggest a new capture session to fill an identified gap.
    Used by: NexusOps (sprint planning).
    """
    return SessionSuggestion(
        suggested_topic="Deep Dive: Redis Cache Invalidation Patterns",
        estimated_duration_mins=20,
        suggested_expert="Lead Backend Engineer"
    )

@router.get("/coverage/{org_id}", response_model=CoverageMap)
async def get_coverage(org_id: str):
    """
    Returns knowledge coverage map.
    Used by: NexusOps (to schedule capture sessions for sparse domains).
    """
    return CoverageMap(
        org_id=org_id,
        domains_covered=["Backend Engineering", "Customer Support"],
        coverage_score=0.64,
        sparse_domains=["Onboarding", "Frontend Architecture"]
    )

# ==============================================================================
# AGENT INTEGRATION EXAMPLES (Documentation)
# ==============================================================================
"""
INTEGRATION PATTERNS FOR OTHER AGENTS:

1. SynthSenior (Code Architect):
    When reviewing legacy code and unable to find "Why was this architectural decision made" in git:
    await client.post("/v1/agentOS/knowledge/query_answer", json={
        "org_id": "org_1",
        "question": "Why does the payment module use a custom exponential backoff?",
        "requesting_agent": "SynthSenior"
    })

2. ThreadSmith (Customer Support Agent):
    Before drafting a response to a complex customer bug report:
    await client.post("/v1/agentOS/knowledge/search", json={
        "org_id": "org_1",
        "query": "Error Code 5003 during checkout",
        "artifact_type": "TROUBLESHOOTING_GUIDE",
        "top_k": 1
    })

3. MeshMed (Clinical Reasoning):
    When generating a care plan and needing the clinic's specific follow-up protocol:
    await client.post("/v1/agentOS/knowledge/query_answer", json={
        "org_id": "org_1",
        "question": "What is the standard follow-up protocol for hypertension patients over 60?",
        "requesting_agent": "MeshMed"
    })
"""
