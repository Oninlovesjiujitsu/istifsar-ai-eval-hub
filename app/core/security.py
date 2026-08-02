from fastapi import Request, HTTPException
from qstash import Receiver
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

async def verify_qstash_signature(request: Request):
    """
    Dependency to verify QStash webhook signature.
    """
    if not settings.QSTASH_CURRENT_SIGNING_KEY:
        logger.warning("QSTASH_CURRENT_SIGNING_KEY is not set. Skipping verification for local dev.")
        return True

    signature = request.headers.get("Upstash-Signature")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing Upstash-Signature header")

    body = await request.body()
    
    try:
        receiver = Receiver(
            current_signing_key=settings.QSTASH_CURRENT_SIGNING_KEY,
            next_signing_key=settings.QSTASH_NEXT_SIGNING_KEY,
        )
        
        # When running behind ngrok/localtunnel, request.url is localhost
        # but QStash signed the public URL. Reconstruct original URL from proxy headers.
        forwarded_host = request.headers.get("x-forwarded-host")
        forwarded_proto = request.headers.get("x-forwarded-proto", "https")
        
        if forwarded_host:
            verification_url = f"{forwarded_proto}://{forwarded_host}{request.url.path}"
        else:
            verification_url = str(request.url)

        receiver.verify(
            body=body.decode("utf-8"),
            signature=signature,
            url=verification_url
        )
    except Exception as e:
        logger.error(f"QStash signature verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid QStash signature")
        
    return True
