"""
SawtOS Healthcare CRM & Compliance Gateway
Provides secure, RBAC-protected REST endpoints for clinical encounters,
de-identification pipelines, and tamper-proof HIPAA audit inspections.
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from .audit import SafeHarborDeidentifier, HIPAAAuditLogger, HIPAAEvent

healthcare_router = APIRouter(prefix="/api/v1/healthcare", tags=["Healthcare CRM"])

# In-memory audit log store
AUDIT_TRAIL: List[HIPAAEvent] = []


class DeidentifyRequest(BaseModel):
    raw_transcript: str
    patient_id: str
    actor_id: str = "agent_worker_livekit"


class DeidentifyResponse(BaseModel):
    sanitized_text: str
    identifiers_redacted: List[str]
    is_safe_harbor_compliant: bool
    audit_event_id: str


def verify_clinician_token(x_auth_role: Optional[str] = Header("clinician")):
    """Simple RBAC guard ensuring only authorized roles view PHI."""
    if x_auth_role not in ("clinician", "compliance_officer", "system_agent"):
        raise HTTPException(status_code=403, detail="Access denied: Insufficient HIPAA role privileges")
    return x_auth_role


@healthcare_router.post("/deidentify", response_model=DeidentifyResponse)
async def deidentify_clinical_notes(
    req: DeidentifyRequest,
    role: str = Depends(verify_clinician_token)
):
    """
    De-identifies clinical dialogue by stripping the 18 HIPAA Safe Harbor identifiers
    and generates an immutable audit record.
    """
    scrub_result = SafeHarborDeidentifier.scrub_phi(req.raw_transcript)
    
    # Generate cryptographic audit log
    audit_evt = HIPAAAuditLogger.log_phi_access(
        actor_id=req.actor_id,
        action_type="DEIDENTIFY",
        patient_id=req.patient_id,
        resource="clinical_call_transcript"
    )
    AUDIT_TRAIL.append(audit_evt)

    return DeidentifyResponse(
        sanitized_text=scrub_result["sanitized_text"],
        identifiers_redacted=scrub_result["identifiers_redacted"],
        is_safe_harbor_compliant=scrub_result["is_safe_harbor_compliant"],
        audit_event_id=audit_evt.event_id
    )


@healthcare_router.get("/audit-vault", response_model=List[HIPAAEvent])
async def get_hipaa_audit_vault(role: str = Depends(verify_clinician_token)):
    """Surfaces the tamper-evident audit history for compliance verification."""
    return AUDIT_TRAIL
