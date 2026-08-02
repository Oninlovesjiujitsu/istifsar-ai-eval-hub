# Istifsar AI Decoupled Evaluation Hub - System Design & Implementation Plan

This document outlines the architecture, tech stack, and phased execution strategy for building the Python-based Evaluation Microservice. Our goal is to ensure a robust, enterprise-grade architecture before writing any execution logic, while adhering strictly to a $0 deployment budget.

## 1. Architecture & Tech Stack

### Core Tech Stack
*   **API Framework:** FastAPI (Python 3.10+)
*   **Web Server:** Uvicorn
*   **Evaluation Framework:** Ragas (Framework for RAG evaluation metrics like Faithfulness and Answer Relevance)
*   **Judge LLM:** Google Gemini (Free Tier: 50 req/day, 2 req/min. Sufficient for manual Historian triggers without needing complex rate-limit logic).
*   **Experiment Tracking:** DagsHub (Provides a fully managed, free remote MLflow tracking URI, preventing data loss on ephemeral disks).
*   **Data Validation:** Pydantic (Strict typing for the incoming payloads)
*   **Database Client:** `supabase-py` (For writing results back to the main DB)
*   **Queue/Broker:** Upstash QStash (Free tier: 500 msgs/day. Handles async delivery and automatic retries during server cold starts).

### System Flow
1.  **Trigger:** Historian flags an anomaly in Next.js, which pushes a payload to QStash.
2.  **Ingestion:** FastAPI `/api/evaluate` endpoint on Render (Free Tier) receives the webhook. (If Render is asleep, QStash will automatically retry upon failure until the server wakes up).
3.  **Security:** FastAPI verifies the QStash cryptographic signature.
4.  **Processing:** Payload is passed to the Ragas evaluation service.
5.  **Evaluation:** Ragas prompts the Gemini Judge LLM to score Faithfulness and Context Relevance.
6.  **Logging:** Results are logged remotely to DagsHub's MLflow server (for MLOps portfolio viewing) and written back to Supabase (for UI display).

## 2. Project Structure

To maintain a clean, modular architecture, the repository will be structured as follows:

```text
istifsar-ai-eval-hub/
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI entry point
│   ├── api/                   # Route handlers
│   │   └── endpoints.py       # POST /evaluate logic
│   ├── models/                # Pydantic data schemas
│   │   └── schemas.py         # TracePayload definition
│   ├── services/              # Business logic
│   │   ├── ragas_service.py   # Gemini LLM Judge integration
│   │   └── db_service.py      # Supabase connection
│   └── core/                  # Configuration and Security
│       ├── config.py          # Environment variables (DagsHub, Supabase, Gemini API keys)
│       └── security.py        # QStash signature verification
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
└── README.md
```

## 3. Implementation Phases

We will execute this project in six distinct phases to ensure stability at each step.

### Phase 1: Foundational API & Security (The Receiver)
*   Initialize the modular folder structure.
*   Define the strict Pydantic schema (`TracePayload`) that exactly matches what Next.js will send.
*   Implement the FastAPI POST endpoint.
*   Implement the QStash signature verification middleware.

### Phase 2: Evaluation Engine Integration (The Judge)
*   Configure the MLflow tracking URI to point to the remote DagsHub server.
*   Set up Ragas with the Gemini API keys for the "Judge LLM".
*   Create the evaluation function that takes the `TracePayload`, runs the metrics, and logs them to DagsHub.

### Phase 3: Database Integration (The State)
*   Initialize the `supabase-py` client.
*   Write the logic to update the specific "Historian Flag" row in Supabase with the calculated evaluation scores and reasoning.

### Phase 4: Local End-to-End Testing
*   Use Postman or cURL to simulate QStash payloads.
*   Verify that the FastAPI server processes the payload, talks to the Gemini judge, logs to DagsHub, and updates Supabase locally without errors.

### Phase 5: Next.js Publisher Setup (in `ai-istifsar`)
*   Switch back to the main `ai-istifsar` repository.
*   Write the TypeScript function that fires the `TracePayload` to QStash when a historian clicks a button in the UI.

### Phase 6: Deployment & Monitoring
*   Deploy the FastAPI application to a single Render free tier account.
*   Point the QStash webhook URL to the live Render endpoint.
*   Rely purely on QStash's built-in retry mechanics to handle Render's cold starts (no cron jobs).
