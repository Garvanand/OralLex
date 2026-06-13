"""
OralLex Core Schemas for Session Management and Real-time Communication.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Dict, Any
from datetime import datetime

# ================================================================
# WEBSOCKET MESSAGES (Client -> Server)
# ================================================================

class AudioChunk(BaseModel):
    type: Literal["audio_chunk"] = "audio_chunk"
    data: str           # base64 encoded audio 
    sequence: int       # for ordering
    timestamp_ms: int

class SessionControl(BaseModel):
    type: Literal["start", "pause", "resume", "end"]
    session_id: str
    metadata: Dict[str, Any]      # topic, expert_name, artifact_types_requested

# ================================================================
# WEBSOCKET MESSAGES (Server -> Client)
# ================================================================

class TranscriptUpdate(BaseModel):
    type: Literal["transcript"] = "transcript"
    text: str
    is_final: bool
    confidence: float
    timestamp_ms: int

class QuestionReady(BaseModel):
    type: Literal["question"] = "question"
    question_text: str
    question_type: str  # "assumption", "edge_case", "causality", "prerequisite"
    triggered_by: str   # the phrase that triggered this question
    priority: int       # 1 = ask now, 2 = ask soon, 3 = ask if time

class SessionStatus(BaseModel):
    type: Literal["status"] = "status"
    knowledge_coverage: float  # 0-1
    questions_pending: int
    session_duration_seconds: int
    transcript_word_count: int

# ================================================================
# STATE MACHINE & ASR SCHEMAS
# ================================================================

class TranscriptionChunk(BaseModel):
    text: str
    is_final: bool
    confidence: float
    word_timestamps: Optional[List[dict]] = None

class Question(BaseModel):
    question_id: str
    text: str
    type: str
    status: Literal["pending", "asked", "answered", "dismissed"]

class KnowledgeGap(BaseModel):
    gap_id: str
    session_id: str
    gap_type: Literal[
        "implicit_assumption", "missing_edge_case", "unexplained_causality",
        "undocumented_prerequisite", "tacit_skill_marker"
    ]
    triggering_phrase: str      # exact words from expert that signaled the gap
    triggering_timestamp_ms: int
    gap_description: str        # what's missing
    importance_score: float     # 0-1, for prioritization
    target_artifact_types: List[str]  # which artifact types need this filled
    generated_question: Optional[str] = None
    was_asked: bool = False
    expert_response: Optional[str] = None   # filled in after expert answers
    is_resolved: bool = False

class KnowledgeNode(BaseModel):
    node_id: str
    concept: str
    depth_of_coverage: float     # how thoroughly was this explained?
    has_gaps: bool
    mentioned_at_ms: List[int]   # timestamps when mentioned

class KnowledgeEdge(BaseModel):
    from_node: str
    to_node: str
    relationship: str            # "causes", "requires", "is_part_of", "example_of"

class KnowledgeGraph(BaseModel):
    nodes: List[KnowledgeNode] = []
    edges: List[KnowledgeEdge] = []
    coverage_score: float = 0.0  # (nodes_fully_covered / total_nodes) × edge_completeness_factor

class TranscriptChunk(BaseModel):
    sequence: int
    text: str
    timestamp: datetime

class SessionState(BaseModel):
    session_id: str
    expert_name: str
    topic: str
    artifact_types: List[str]
    status: Literal["initializing", "active", "paused", "completing", "complete"]
    transcript_chunks: List[TranscriptChunk] = []
    full_transcript: str = ""
    knowledge_graph: KnowledgeGraph = Field(default_factory=KnowledgeGraph)
    questions_asked: List[Question] = []
    questions_pending: List[Question] = []
    coverage_score: float = 0.0
    session_start: datetime = Field(default_factory=datetime.utcnow)
    total_speaking_time_seconds: int = 0
    last_pause_at: Optional[datetime] = None

class PauseEvent(BaseModel):
    pause_type: Literal["natural", "mid_thought", "end_of_thought", "topic_completion"]
    duration_ms: int
    should_ask_question: bool
    reasoning: str

# ================================================================
# ARTIFACT GENERATION & QUALITY CONTROL
# ================================================================

class KnowledgeArtifact(BaseModel):
    artifact_id: str
    session_id: str
    artifact_type: str
    title: str
    markdown_content: str
    generated_at: datetime
    status: Literal["draft", "reviewed", "published"]

class HallucinationReport(BaseModel):
    passed: bool
    unsupported_claims: List[str]
    confidence_score: float

class CompletenessReport(BaseModel):
    passed: bool
    missing_resolved_gaps: List[str]
    unresolved_gaps_flagged: bool

class StructureReport(BaseModel):
    passed: bool
    missing_sections: List[str]
    empty_sections: List[str]

class DeduplicationResult(BaseModel):
    action: Literal["create_new", "suggest_merge", "auto_link"]
    similar_artifact_id: Optional[str] = None
    similarity_score: float = 0.0
    reasoning: str

# ================================================================
# PUBLISHING & INTEGRATIONS
# ================================================================

class PublishConfig(BaseModel):
    destination: Literal["notion", "confluence", "markdown_file", "agentOS"]
    notion_database_id: Optional[str] = None
    confluence_space_key: Optional[str] = None
    parent_page_id: Optional[str] = None
    org_id: Optional[str] = None

class PublishResult(BaseModel):
    success: bool
    url: Optional[str] = None
    error_message: Optional[str] = None
    published_at: Optional[datetime] = None

# ================================================================
# REPLAY & ANNOTATION
# ================================================================

class Annotation(BaseModel):
    annotation_id: str
    session_id: str
    transcript_start_ms: int
    transcript_end_ms: int
    highlighted_text: str
    annotation_type: Literal[
        "important",     # prioritize in artifact
        "delete",        # remove from artifact
        "expand",        # generate follow-up questions
        "private",       # exclude from published artifact
        "needs_review",  # flag for human review
        "add_context"    # expert adds additional text
    ]
    added_context: Optional[str] = None
    created_at: datetime

class PublishedArtifact(BaseModel):
    artifact_id: str
    destination: str
    url: str
    published_at: datetime

class SessionReplay(BaseModel):
    session_id: str
    transcript: List[TranscriptChunk]
    knowledge_gaps: List[KnowledgeGap]
    questions_asked: List[Question]
    audio_url: Optional[str] = None
    annotations: List[Annotation]
    generated_artifacts: List[KnowledgeArtifact]
    published_artifacts: List[PublishedArtifact]

class ExpansionSession(BaseModel):
    session_id: str
    parent_session_id: str
    focus_topic: str
    preloaded_questions: List[str]
    status: Literal["pending", "active", "completed"]
