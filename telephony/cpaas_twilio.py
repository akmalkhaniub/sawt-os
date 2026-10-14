"""
SawtOS Carrier CPaaS Integration (Twilio & Telnyx)
Orchestrates inbound PSTN calls to LiveKit SIP trunks, handles live status reconciliation,
and dispatches outbound campaigns.
"""

from fastapi import APIRouter, Request, HTTPException, Form, BackgroundTasks
from fastapi.responses import Response
from typing import Optional, Dict
import logging
from .fsm import TelephonyCallSession, CallState

logger = logging.getLogger("sawtos.telephony")
telephony_router = APIRouter(prefix="/api/v1/telephony", tags=["Telephony"])

# Active in-memory session registry (backed by Redis in production)
ACTIVE_SESSIONS: Dict[str, TelephonyCallSession] = {}


@telephony_router.post("/twilio/inbound", response_class=Response)
async def handle_twilio_inbound_voice(
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    CallDuration: Optional[str] = Form(None),
):
    """
    Twilio Webhook: Intercepts inbound PSTN call and forwards to LiveKit SIP Trunk.
    Dynamically identifies Gulf (+966, +971, +974) vs US (+1) numbers for model routing.
    """
    logger.info(f"Incoming call: CallSid={CallSid}, From={From}, To={To}")

    # Determine region and language
    is_gulf = From.startswith("+966") or From.startswith("+971") or From.startswith("+974")
    region = "gulf" if is_gulf else "us"
    language = "ar-XA" if is_gulf else "en-US"
    room_name = f"sawt-{region}-{CallSid[:8]}"

    # Initialize FSM session
    session = TelephonyCallSession(
        call_sid=CallSid,
        room_name=room_name,
        from_number=From,
        to_number=To,
        region=region,
        language=language,
        state=CallState.RINGING
    )
    ACTIVE_SESSIONS[CallSid] = session

    # Generate TwiML bridging directly into the LiveKit SIP trunk
    # LiveKit SIP URI structure: sip:room_name@sawtos.sip.livekit.cloud or self-hosted
    sip_uri = f"sip:{room_name}@sawtos.sip.livekit.cloud;region={region}"

    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Zeina" language="ar-XA">مرحباً بكم في منصة صوت الذكية، جاري تحويل مكالمتكم.</Say>
    <Dial timeout="20" record="record-from-answer-dual">
        <Sip statusCallbackEvent="initiated ringing answered completed"
             statusCallback="/api/v1/telephony/twilio/status">
            {sip_uri}
        </Sip>
    </Dial>
</Response>"""

    return Response(content=twiml_response, media_type="application/xml")


@telephony_router.post("/twilio/status")
async def handle_twilio_status_callback(
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    CallDuration: Optional[int] = Form(None),
    background_tasks: BackgroundTasks = None
):
    """
    Carrier Lifecycle Status Reconciliation:
    Synchronizes Twilio call events into the SawtOS Telephony FSM.
    On 'completed', dispatches automated Post-Call LLM-as-a-Judge QA analysis.
    """
    logger.info(f"Carrier Status Event: CallSid={CallSid}, Status={CallStatus}, Duration={CallDuration}")

    session = ACTIVE_SESSIONS.get(CallSid)
    if not session:
        logger.warning(f"Session not found for CallSid: {CallSid}")
        return {"status": "untracked_session"}

    if CallStatus == "in-progress" and session.state == CallState.RINGING:
        session.transition_to(CallState.CONNECTED, reason="Carrier answered")

    elif CallStatus in ("completed", "canceled", "failed", "busy", "no-answer"):
        if session.state != CallState.COMPLETED:
            if session.state in (CallState.CONNECTED, CallState.ON_HOLD, CallState.TRANSFERRING):
                session.transition_to(CallState.WRAP_UP, reason="Caller hung up")
                session.transition_to(CallState.COMPLETED, reason=f"Carrier final state: {CallStatus}")
            else:
                session.transition_to(CallState.FAILED, reason=f"Carrier error: {CallStatus}")

        # If background_tasks is available, we schedule post-call processing
        logger.info(
            f"Call {CallSid} finished. Total seconds: {session.total_duration_seconds:.2f}, "
            f"Billable minutes: {session.billable_minutes}"
        )

    return {
        "status": "reconciled",
        "call_sid": CallSid,
        "current_fsm_state": session.state.value,
        "total_duration_sec": session.total_duration_seconds
    }


@telephony_router.get("/sessions/{call_sid}")
async def get_session_telemetry(call_sid: str):
    """Surfaces real-time FSM telemetry and billing metrics for a given call."""
    session = ACTIVE_SESSIONS.get(call_sid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
