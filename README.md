---
title: Project Chimera
emoji: 🛡️
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# Project Chimera: AI-Native Threat Matrix

An OpenEnv environment designed to evaluate frontier LLMs on their ability to identify and exploit complex logic flaws in AI-generated code.

## Environment Details
- **Observation Space**: System architecture JSON, code snippets, and fuzzing telemetry.
- **Action Space**: `analyze`, `probe`, `exploit` with concurrent payload sequences.
- **Task Focus**: Time-of-Check to Time-of-Use (TOCTOU) Race Conditions.

## Quick Start
To run the baseline inference locally against the deployed environment:
1. Set `HF_TOKEN` and `MODEL_NAME`.
2. Run `python inference.py`.