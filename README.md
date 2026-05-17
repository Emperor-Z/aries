# Ares / Aries

Local multi-agent AI system for running specialised assistants on a personal machine. Ares combines local Ollama models, role-specific agents, A2A HTTP services, memory, Serena code-navigation integration, and Langfuse observability behind a terminal REPL.

## What It Does

- Routes prompts through an orchestrator agent
- Provides direct agent commands for coder, thinker, runner, and Serena workflows
- Runs local models through Ollama instead of hosted model APIs
- Exposes A2A health endpoints for individual agents
- Tracks runs through a local/self-hosted Langfuse stack
- Includes a learning cycle hook for memory and behaviour refinement experiments

## Architecture

```text
Terminal REPL
    |
    v
AresSystem
    |
    +-- orchestrator agent
    +-- coder agent
    +-- thinker agent
    +-- runner agent
    +-- Serena/code-navigation agent
    |
    +-- Ollama local models
    +-- memory layer
    +-- Langfuse observability
    +-- A2A HTTP services (:8100-:8104)
```

## Commands

```text
/coder <task>    code-focused task execution
/thinker <task>  deeper reasoning or planning
/runner <task>   quick execution-oriented task
/serena <task>   codebase-aware navigation and edits
/learn           run the learning cycle
/quit            exit the REPL
```

## Requirements

- Python 3.13 environment used by the paired `ares-core` checkout
- Ollama with the configured local models pulled
- Docker and Docker Compose for the Langfuse stack
- Local `ares-core` directory next to this repository

The current scripts expect this layout:

```text
parent-directory/
  aries/
  ares-core/
```

## Configuration

Set Langfuse keys in your shell or a local environment file before running the startup script:

```bash
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
```

Do not commit real keys. The repository intentionally does not store production or personal secrets.

## Quickstart

```bash
./start.sh
```

The script checks or starts:

- Ollama on `localhost:11434`
- Langfuse on `localhost:3000`
- A2A agent services on ports `8100` to `8104`
- the terminal REPL through `main.py`

## Status

This is an experimental personal AI system. It is useful as a portfolio project for local AI orchestration, but it still assumes a local machine layout and model setup. Next improvements should include a one-command installer, sample config, automated tests, and Dockerised agent services.
