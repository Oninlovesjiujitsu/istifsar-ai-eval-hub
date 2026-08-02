from supabase import create_client, Client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def get_supabase_client() -> Client | None:
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        logger.warning("Supabase credentials are not set. Database updates will be skipped.")
        return None
        
    # We use the SERVICE_ROLE key here because this is a trusted backend microservice.
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

def update_evaluation_scores(record_id: str, scores: dict):
    """
    Updates the specific record in Supabase with the evaluation scores.
    """
    supabase = get_supabase_client()
    if not supabase:
        return {"status": "skipped", "reason": "No Supabase configuration"}
        
    try:
        # We target the 'messages' table in ai-istifsar which stores the AI's generated response
        response = (
            supabase.table("messages") 
            .update({
                "faithfulness_score": scores.get("faithfulness"),
                "relevancy_score": scores.get("answer_relevancy"),
                "is_hallucination_flagged": True, # Flagged by historian
                "evaluation_status": "completed"
            })
            .eq("id", record_id)
            .execute()
        )
        logger.info(f"Supabase update successful for record {record_id}")
        return {"status": "success", "data": response.data}
    except Exception as e:
        logger.error(f"Failed to update Supabase for record {record_id}: {e}")
        return {"status": "error", "error": str(e)}
