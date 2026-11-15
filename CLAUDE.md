# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Study Buddy: a RAG chatbot over the user's personal lecture notes. A FastAPI backend (Python, LangChain/LangGraph, ChromaDB) serves a Vue 3 + Vite frontend. No tests, linter, or README exist; `requirements.txt` is empty (deps live in `.venv`, so don't trust it). The project is not a git repository.

## Commands

Backend (from repo root, using the `.venv` virtualenv; `ANTHROPIC_API_KEY` is read from `.env`):
- `python ingestion.py` — load `./notes/**/*.txt`, chunk, embed, and write to `./chroma_db`
- `python agent.py` — interactive CLI loop to query the agent
- `uvicorn server:app --reload --port 8000` — run the API (the frontend hardcodes `http://localhost:8000`)

Frontend (from `frontend/`):
- `npm run dev` — Vite dev server
- `npm run build` — `vue-tsc -b && vite build` (type-check + build)

## Architecture

Pipeline: notes → `ingestion.py` → Chroma vector store → `agent.py` retriever tool → LangGraph ReAct agent → `server.py` endpoints → Vue UI.

- `ingestion.py`: `load_and_split_notes()` (DirectoryLoader, 1000-char chunks, 200 overlap) and `store_chunks_in_vector_db()` (Chroma.from_documents persisted to `./chroma_db`). Note the loader glob is `**/*.txt` only, even though the UI and comments mention `.md`.
- `agent.py`: `initialize_agent()` builds a Chroma retriever (k=3) wrapped as the `student_notes_search` tool, and a `create_react_agent` with a system prompt requiring answers from notes only, with source citations. Embedding model (`sentence-transformers/all-MiniLM-L6-v2`) must match between `ingestion.py` and `agent.py`.
- `server.py`: `POST /upload` saves a file to `./notes` and re-ingests all notes; `POST /ask` invokes the agent with `{"question": ...}` and returns `{"answer": ...}`. CORS is wide open.
- `frontend/src/services/api.js` (axios client) is used by `frontend/src/App.vue` (sidebar upload + chat UI). `HelloWorld.vue` is leftover Vite scaffold.

## Known issues to be aware of

- `server.py` does `from agent import agent_executor`, but `agent.py` only defines `initialize_agent()` and creates the executor under `__main__`, so the server fails to import. Fix by calling `agent_executor = initialize_agent()` in `server.py` (or at module level in `agent.py`).
- Re-ingestion on every upload calls `Chroma.from_documents` over all notes without clearing the DB, so existing chunks get duplicated. The agent also won't see new data until its vector store is reloaded/queried afresh.
- `ChatAnthropic(model="claude-sonnet-5")` in `agent.py` — verify this is a valid model ID.
