# 📜 Istifsar AI: Evaluation Hub

The companion microservice to **Istifsar AI**. This decoupled backend is responsible for the asynchronous evaluation of RAG responses, utilizing the Ragas framework to automatically grade AI answers for faithfulness and relevancy. 

## 📦 Technologies

- `FastAPI` (Python)
- `Ragas` (Evaluation Framework)
- `Google Gemini` (Flash 2.5, gemini-embedding-001)
- `Upstash QStash` (Message Queues & Webhooks)
- `MLflow` & `DagsHub` (MLOps Telemetry & Tracking)
- `Supabase` (PostgreSQL sync)
- `Uvicorn`

## 🦄 Features

- **Asynchronous Decoupling**: Heavy LLM evaluation tasks (which take time) are completely decoupled from the Next.js frontend using Upstash QStash. Users can flag responses and immediately continue chatting without UI blocking.
- **Reference-Free Evaluation**: Utilizes `faithfulness` and `answer_relevancy` metrics from Ragas to grade the AI's response strictly against the retrieved historical context.
- **MLOps Observability**: Every evaluation run is tracked, scored, and logged remotely to DagsHub via MLflow, creating a comprehensive telemetry history of model performance.
- **Automatic Data Sync**: Upon completion, the evaluation scores are automatically pushed back into the primary Supabase `messages` table, seamlessly updating the frontend UI.

## 👩🏽‍🍳 The Process

Istifsar's core constraint—*"No Document, No History"*—requires rigorous evaluation. Relying purely on the LLM to govern itself is insufficient. 

**Stack choice:** FastAPI for rapid Python microservice development, Ragas for standard LLM metrics, Gemini 2.5 Flash (to mirror the RAG embedding models), and QStash for bulletproof webhook delivery.

**The Pipeline:**
When a user flags a message in the Next.js app ➡️ QStash queues the webhook ➡️ FastAPI receives the payload and pushes it to a BackgroundTask ➡️ Ragas evaluates the `query`, `generated_answer`, and `retrieved_context` ➡️ MLflow logs the run to DagsHub ➡️ Supabase is updated with the final decimals (`faithfulness_score`, `relevancy_score`).

## 📚 What I Learned

- **Decoupling is mandatory for LLM evals:** Running Ragas directly in a Next.js API route leads to Vercel timeouts and terrible UX. Offloading to a Python microservice via QStash solves this gracefully.
- **Evaluation requires the same embedding models:** Ragas defaults to OpenAI. It was critical to manually override both the generator LLM and the evaluator Embedding model to use Google's `models/gemini-embedding-001` to ensure the vector space matched the main application.
- **Object Parsing in Ragas:** Newer versions of Ragas return complex `EvaluationResult` objects (Pandas DataFrames) rather than simple dictionaries, requiring careful type extraction before pushing to strict metric trackers like MLflow.

## 🚦 Running the Project

To run the project in your local environment, follow these steps:

1. Clone the repository to your local machine.
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and add your credentials:
   ```
   # QStash (From Upstash Dashboard)
   QSTASH_CURRENT_SIGNING_KEY=your_key
   QSTASH_NEXT_SIGNING_KEY=your_key

   # MLflow (DagsHub)
   MLFLOW_TRACKING_URI=https://dagshub.com/...
   MLFLOW_TRACKING_USERNAME=your_username
   MLFLOW_TRACKING_PASSWORD=your_token

   # Gemini API
   GOOGLE_API_KEY=your_gemini_key

   # Supabase
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_KEY=your_service_role_key
   ```
5. Start the FastAPI server:
   ```bash
   python -m uvicorn app.main:app --reload
   ```
6. Expose the port using localtunnel or ngrok (for QStash webhooks):
   ```bash
   npx localtunnel --port 8000
   ```

## ☁️ Deployment Considerations (Free Tiers)

If you deploy this microservice to a free tier hosting provider (like Render or Railway), the server will automatically "spin down" after a period of inactivity.

**The Cold Start Problem:** When a user flags a message, the free-tier backend might take 50+ seconds to wake up from sleep, which normally causes standard HTTP requests to timeout and fail. 

**The QStash Solution:** Because this architecture relies on Upstash QStash, **cold starts are not an issue**. QStash automatically handles timeouts and retries the webhook delivery using exponential backoff. You will never lose an evaluation payload; the very first evaluation after inactivity will just take an extra minute to appear in Supabase while the server boots up.
