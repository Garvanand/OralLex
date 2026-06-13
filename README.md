# Day 05: OralLex

OralLex is the **Socratic Knowledge Extraction Engine** for AgentOS. 

When human experts try to document their workflows, they unconsciously skip steps that feel "obvious" to them. These omissions are precisely why most corporate documentation is useless. OralLex solves this by functioning as an active, Socratic listener. It monitors the expert as they speak, detects these knowledge gaps in real-time, and generates structured, high-quality artifacts (SOPs, FAQs, Decision Trees) that are instantly published to your organization's knowledge base.

## Core Features

- **Socratic Gap Detection**: Uses advanced LLM pipelines to actively listen and detect 5 types of knowledge gaps in real-time:
  1. *Implicit Assumptions* ("we always do X")
  2. *Missing Edge Cases* (happy path only)
  3. *Prerequisite Omissions* (assuming tools are already set up)
  4. *Tacit Skill Flags* ("you just have to feel when it's right")
  5. *Causality Gaps* ("X happens, then Z happens" - what about Y?)
- **Knowledge Artifact Generator**: Converts raw transcripts and resolved gaps into highly structured artifacts:
  - Standard Operating Procedures (SOPs)
  - FAQs
  - Decision Trees (with Markdown flowchart exports)
  - Troubleshooting Guides
- **Frictionless UI (`session.html`)**: A clean, single-file React+Tailwind interface that stays out of the expert's way. It displays a rolling transcript and elegantly queues Socratic questions for the expert to answer organically.
- **Notion Integration**: Automatically converts markdown artifacts into native Notion blocks and publishes them directly to the company workspace.
- **AgentOS Knowledge Graph**: Writes to `agentOS:memory:knowledge:{org_id}` so that other agents (like SynthSenior, ThreadSmith, and MeshMed) can instantly leverage the newly captured expert knowledge.

## Prerequisites

- Docker and Docker Compose
- Python 3.10+
- Notion API Integration Token

## Setup

1. Navigate to the project directory:
   ```bash
   cd Day05_OralLex
   cp .env.example .env
   # Insert your LLM API keys and Notion integration token
   ```

2. Run alongside the AgentOS ecosystem:
   ```bash
   docker-compose -f ../docker-compose.yml -f docker-compose.extension.yml up -d --build
   ```

## Development

To run locally without Docker:
```bash
pip install -r requirements.txt
uvicorn oralex.api.server:app --reload --port 8004
```
