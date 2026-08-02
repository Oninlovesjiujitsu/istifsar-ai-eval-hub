import os
import mlflow
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from datasets import Dataset
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from app.models.schemas import TracePayload
from app.core.config import settings
import google.generativeai as genai

def setup_ragas_and_mlflow():
    # Initialize Gemini LLM and Embeddings for Ragas (Ragas uses LangChain underneath)
    if settings.GOOGLE_API_KEY:
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        # Using gemini-1.5-pro as it's the strongest reasoning model available in the free tier
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=settings.GOOGLE_API_KEY)
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=settings.GOOGLE_API_KEY)
    else:
        llm = None
        embeddings = None
        print("WARNING: GOOGLE_API_KEY is not set. Ragas evaluation will fail.")

    # Configure MLflow to point to DagsHub
    if settings.MLFLOW_TRACKING_URI:
        os.environ["MLFLOW_TRACKING_USERNAME"] = settings.MLFLOW_TRACKING_USERNAME
        os.environ["MLFLOW_TRACKING_PASSWORD"] = settings.MLFLOW_TRACKING_PASSWORD
        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
        mlflow.set_experiment("Istifsar_AI_Evaluations")
    else:
        print("WARNING: MLFLOW_TRACKING_URI is not set. Metrics will not be logged remotely.")
        
    return llm, embeddings

def evaluate_trace_with_ragas(payload: TracePayload) -> dict:
    """
    Evaluates the trace using Ragas metrics and logs results to DagsHub.
    """
    llm, embeddings = setup_ragas_and_mlflow()
    
    if not llm or not embeddings:
        return {"error": "LLM or Embeddings not configured"}

    # Ragas requires data in HuggingFace Dataset format
    data = {
        "question": [payload.query],
        "answer": [payload.generated_answer],
        "contexts": [payload.retrieved_context],
        "ground_truth": [""] # Optional, omitted since we are doing reference-free evaluation
    }
    dataset = Dataset.from_dict(data)

    # Start MLflow run
    with mlflow.start_run(run_name=f"eval_{payload.record_id}"):
        # Log payload metadata
        mlflow.log_param("record_id", payload.record_id)
        mlflow.log_param("query", payload.query)
        mlflow.log_param("historian_flagged", True)
        
        if payload.historian_notes:
            mlflow.log_param("historian_notes", payload.historian_notes)
        
        try:
            # Execute Ragas Evaluation (Faithfulness & Relevancy)
            result = evaluate(
                dataset=dataset,
                metrics=[faithfulness, answer_relevancy],
                llm=llm,
                embeddings=embeddings
            )
            
            # In newer versions of Ragas, result["metric_name"] might return a list or pandas Series
            def safe_float(key):
                try:
                    val = result[key]
                    if hasattr(val, "tolist"):
                        val = val.tolist()
                    if isinstance(val, list):
                        return float(val[0]) if len(val) > 0 else 0.0
                    return float(val)
                except Exception:
                    return 0.0
                    
            scores = {
                "faithfulness": safe_float("faithfulness"),
                "answer_relevancy": safe_float("answer_relevancy")
            }
            
            # Log metrics to DagsHub
            mlflow.log_metrics(scores)
            print(f"Evaluation complete for {payload.record_id}. Scores: {scores}")
            
            return scores
            
        except Exception as e:
            print(f"Error during Ragas evaluation: {e}")
            mlflow.log_param("error", str(e))
            return {"error": str(e)}
