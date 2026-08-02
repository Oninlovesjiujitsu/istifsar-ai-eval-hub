from fastapi import APIRouter, Depends, BackgroundTasks
from app.models.schemas import TracePayload
from app.core.security import verify_qstash_signature
from app.services.ragas_service import evaluate_trace_with_ragas
from app.services.db_service import update_evaluation_scores
import traceback

router = APIRouter()

def process_evaluation_task(payload: TracePayload):
    """
    Background task that calls Ragas and logs to MLflow (DagsHub).
    """
    print(f"Background processing started for record_id: {payload.record_id}")
    try:
        scores = evaluate_trace_with_ragas(payload)
        
        # Write the scores back to Supabase so the Historian's UI can see them
        if "error" not in scores:
            update_evaluation_scores(payload.record_id, scores)
            
    except Exception as e:
        print(f"Failed to evaluate trace {payload.record_id}: {e}")
        traceback.print_exc()

@router.post("/evaluate", dependencies=[Depends(verify_qstash_signature)])
async def evaluate_trace(payload: TracePayload, background_tasks: BackgroundTasks):
    """
    Receives the flagged trace from QStash and queues the evaluation.
    """
    print(f"Received flagged anomaly for record: {payload.record_id}")
    
    # Hand off the heavy ML evaluation to a background task so we return 200 OK to QStash immediately.
    background_tasks.add_task(process_evaluation_task, payload)
    
    return {
        "status": "success", 
        "message": "Payload received. Evaluation queued in background."
    }
