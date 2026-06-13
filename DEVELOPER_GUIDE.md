# OralLex Developer Guide

This guide is for developers maintaining or expanding the OralLex knowledge extraction system.

## Expanding the Gap Detector

The intelligence of OralLex lies in its ability to detect when an expert skips a step. The 5 current gap categories are defined in `oralex/intelligence/gap_detector.py`.

To add a new gap category:
1. Define the new category enum (e.g., `REGULATORY_COMPLIANCE_OMISSION`).
2. Add triggering keywords to the heuristic filter (e.g., "approve", "sign off", "legal").
3. Update the LLM evaluation prompt to instruct the model on how to formulate a question for this specific gap (e.g., *"If the expert mentions an approval step, ask 'Who is the specific authority required to sign off on this?'"*).

## Adding New Artifact Types

Currently, `oralex/artifacts/generator.py` generates SOPs, FAQs, Decision Trees, and Troubleshooting Guides.

To add a new format (like `API_DOCUMENTATION` or `ONBOARDING_CHECKLIST`):
1. Add the type to the `ArtifactType` Enum.
2. Create a new prompt template detailing the exact Markdown structure required for the output.
3. Update the Notion publisher in `oralex/integrations/notion.py` if the new artifact type introduces complex Markdown elements (like Mermaid.js diagrams) that require specific Notion block conversions.

## Evaluation Harness

OralLex includes a synthetic evaluation harness in `oralex/eval/harness.py`. It tests the Gap Detector against 5 synthetic expert sessions containing exactly 23 planted knowledge gaps (prerequisites, edge cases, etc.).

Before committing changes to the `gap_detector.py` logic, run the harness:
```bash
python -m oralex.eval.harness
```
Ensure the detection rate remains above the 90% threshold and the hallucination rate (asking irrelevant questions) remains at 0%.
