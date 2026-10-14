"""
SawtOS Main FastAPI Gateway
Unifies Carrier Telephony, In-Call RAG, Post-Call LLM-as-a-Judge,
LiveKit WebRTC Token Issuance, and HIPAA Healthcare CRM.
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Internal routers
from telephony.cpaas_twilio import telephony_router
from healthcare.main import healthcare_router
from analytics.rag_engine import InCallRAGEngine
from analytics.post_call_judge import PostCallJudge

# LiveKit token issuance (with graceful fallback for lightweight runtime environments)
try:
    from livekit import api as livekit_api
except ImportError:
    livekit_api = None
app = FastAPI(
    title="SawtOS: Carrier-Grade Voice AI & Telephony Platform",
    description="Orchestrator for LiveKit Real-Time Agents, Twilio/Telnyx SIP Trunks, In-Call RAG & HIPAA Healthcare Pipelines",
    version="1.0.0"
)

# CORS configuration for Next.js frontend HUD
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount core routers
app.include_router(telephony_router)
app.include_router(healthcare_router)

# RAG & QA singletons
rag_engine = InCallRAGEngine()
qa_judge = PostCallJudge()


class LiveKitTokenRequest(BaseModel):
    room_name: str
    participant_identity: str
    participant_name: Optional[str] = "Web Caller"
    region: Optional[str] = "gulf"


class InCallRAGRequest(BaseModel):
    query: str
    top_k: Optional[int] = 2


class PostCallEvaluationRequest(BaseModel):
    call_sid: str
    transcript: str
    region: Optional[str] = "gulf"


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "SawtOS Enterprise Voice Core",
        "version": "1.0.0",
        "telephony_engine": "LiveKit SIP v1.1 + Twilio",
        "voice_pipeline": "Dual-Engine (Gemini Live S2S / Cascaded Deepgram-Groq-Cartesia)"
    }


@app.post("/api/v1/livekit/token")
async def generate_livekit_token(req: LiveKitTokenRequest):
    """
    Issues ephemeral WebRTC JWT tokens for client browsers to connect directly
    to LiveKit voice agent rooms with low latency.
    """
    api_key = os.getenv("LIVEKIT_API_KEY", "devkey")
    api_secret = os.getenv("LIVEKIT_API_SECRET", "secret")
    if livekit_api:
        token = (
            livekit_api.AccessToken(api_key, api_secret)
            .with_identity(req.participant_identity)
            .with_name(req.participant_name)
            .with_grants(livekit_api.VideoGrants(
                room_join=True,
                room=req.room_name,
                can_publish=True,
                can_subscribe=True,
            ))
        )
        jwt_token = token.to_jwt()
    else:
        # High-fidelity JWT mock for test/demo environments without livekit SDK
        import base64, hmac, hashlib, json
        header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').decode().rstrip('=')
        payload = base64.urlsafe_b64encode(json.dumps({
            "sub": req.participant_identity,
            "room": req.room_name,
            "name": req.participant_name,
            "region": req.region
        }).encode()).decode().rstrip('=')
        sig = hmac.new(api_secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).hexdigest()
        jwt_token = f"{header}.{payload}.{sig}"

    return {
        "token": jwt_token,
        "room_name": req.room_name,
        "region": req.region,
        "ws_url": os.getenv("LIVEKIT_URL", "ws://localhost:7880")
    }


@app.post("/api/v1/rag/query")
async def query_in_call_rag(req: InCallRAGRequest):
    """Sub-4ms hybrid semantic retrieval for live agent knowledge grounding."""
    results = await rag_engine.search(query=req.query, top_k=req.top_k or 2)
    return {"query": req.query, "results": results}


@app.post("/api/v1/analytics/evaluate")
async def evaluate_call_qa(req: PostCallEvaluationRequest):
    """Executes automated post-call LLM-as-a-Judge QA & Compliance evaluation."""
    scorecard = await qa_judge.evaluate_call(
        call_sid=req.call_sid,
        transcript=req.transcript,
        region=req.region or "gulf"
    )
    return scorecard


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
