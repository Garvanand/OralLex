"""
OralLex Artifact Generation Prompts.

Distinct prompts for transforming raw transcripts and resolved gaps into 
highly structured knowledge artifacts (SOPs, FAQs, Decision Trees, etc).
"""

from langchain_core.prompts import ChatPromptTemplate

# Base instructions applied to ALL artifact types
BASE_RULES = """
CRITICAL RULES FOR ALL KNOWLEDGE ARTIFACTS:
1. NO HALLUCINATION: You must not invent, infer, or assume any information not explicitly stated in the transcript or resolved gaps.
2. CITE SOURCES: When stating a specific fact, rule, or number, include a brief inline citation quoting the expert (e.g., *"deployments always fail if... "*).
3. FLAG GAPS: If a required section of the structure cannot be filled because the expert did not address it, output: "> [!WARNING]\n> Note: The expert did not address this area." Do NOT fill it with general industry knowledge.
4. INCORPORATE RESOLVED GAPS: Pay special attention to the `RESOLVED_GAPS` section. These represent deep tacit knowledge excavated during the session. Integrate them naturally.
"""

SOP_SYSTEM = BASE_RULES + """
You are generating a STANDARD OPERATING PROCEDURE (SOP).
Structure your Markdown EXACTLY like this:

# [Title]
**Purpose and Scope**: [Brief summary]

## Prerequisites
[List items specifically drawn from undocumented_prerequisite gaps]

## Procedure
[Step-by-step numbered list. Include decision points if applicable]

## Exception Handling
[List specific failure modes and edge cases drawn from missing_edge_case gaps]

## Verification
[How to know it worked]
"""

FAQ_SYSTEM = BASE_RULES + """
You are generating a FREQUENTLY ASKED QUESTIONS (FAQ) document.
Organize Q&As by logical topic. 

For each Q&A:
**Q:** [Question]
**A:** [Concise answer]. 
*Context:* [Optional quote or background from the transcript]
"""

DECISION_TREE_SYSTEM = BASE_RULES + """
You are generating a DECISION TREE.
Structure your Markdown EXACTLY like this:

# [Title]

## Logic Flow
[Bullet point structure showing nested IF/THEN conditions based heavily on unexplained_causality gaps]

## Mermaid Diagram
```mermaid
graph TD
[Generate a valid Mermaid flowchart representing the logic]
```
"""

TROUBLESHOOTING_SYSTEM = BASE_RULES + """
You are generating a TROUBLESHOOTING GUIDE.
Structure your Markdown EXACTLY like this:

# [Title]

## Symptoms
[Describe the problem states]

## Diagnostic Path
1. [Question to ask / Check to perform]
2. [Next check]

## Root Causes & Solutions
- **Cause 1**: [from unexplained_causality gaps]
  - **Solution**: [action]
"""

TUTORIAL_SYSTEM = BASE_RULES + """
You are generating a TUTORIAL.
Focus on learning objectives and conceptual overview before diving into examples. Ensure you highlight "Common Mistakes" using data from `missing_edge_case` gaps.
"""

CASE_STUDY_SYSTEM = BASE_RULES + """
You are generating a CASE STUDY.
Structure your Markdown EXACTLY like this:

# [Title]
## Situation
## Challenge
## Decision Process
[Highlight the expert's tacit reasoning, specifically drawing from tacit_skill_marker gaps]
## Actions Taken
## Outcome & Lessons Learned
"""

# Factory for generating the right prompt based on type
def get_artifact_prompt(artifact_type: str) -> ChatPromptTemplate:
    systems = {
        "SOP": SOP_SYSTEM,
        "FAQ": FAQ_SYSTEM,
        "DECISION_TREE": DECISION_TREE_SYSTEM,
        "TROUBLESHOOTING_GUIDE": TROUBLESHOOTING_SYSTEM,
        "TUTORIAL": TUTORIAL_SYSTEM,
        "CASE_STUDY": CASE_STUDY_SYSTEM
    }
    
    system_prompt = systems.get(artifact_type, SOP_SYSTEM)
    
    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """
<SESSION_TRANSCRIPT>
{transcript}
</SESSION_TRANSCRIPT>

<RESOLVED_GAPS>
{resolved_gaps}
</RESOLVED_GAPS>

Generate the {artifact_type} in pure Markdown format.
""")
    ])
