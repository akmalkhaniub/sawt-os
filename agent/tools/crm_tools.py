"""
SawtOS Enterprise CRM & Clinical Voice Tools
Exposed as function tools to the LiveKit voice agents (Gemini Live and PydanticAI/Groq).
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger("sawtos.tools")

# Mock CRM Database for live call operations
MOCK_PATIENT_DB = {
    "+14155552671": {
        "patient_id": "PT-90210",
        "name": "Sarah Connor",
        "jurisdiction": "US",
        "dob": "1984-05-12",
        "insurance_active": True,
        "primary_physician": "Dr. Peter Silberman",
        "last_encounter": "2026-08-14 (Cardiology Follow-up)",
        "security_pin": "1984",
    },
    "+966501234567": {
        "patient_id": "PT-KSA-4412",
        "name": "Faisal Al-Otaibi (فيصل العتيبي)",
        "jurisdiction": "Gulf (Riyadh, KSA)",
        "dob": "1990-11-03",
        "insurance_active": True,
        "primary_physician": "Dr. Tariq Al-Ghamdi (د. طارق الغامدي)",
        "last_encounter": "2026-09-20 (Endocrinology Consultation)",
        "security_pin": "9988",
    }
}


class CallerProfile(BaseModel):
    patient_id: str
    name: str
    jurisdiction: str
    is_verified: bool
    summary: str


class AppointmentConfirmation(BaseModel):
    booking_id: str
    patient_id: str
    specialty: str
    scheduled_time: str
    status: str


def lookup_caller_context(phone_number: str) -> Dict[str, Any]:
    """
    Retrieves caller clinical profile and account tier based on inbound caller ID.
    Supports both US (+1) and Gulf (+966, +971) phone numbers.
    """
    logger.info(f"Executing lookup_caller_context for {phone_number}")
    record = MOCK_PATIENT_DB.get(phone_number)
    if record:
        return {
            "found": True,
            "patient_id": record["patient_id"],
            "name": record["name"],
            "jurisdiction": record["jurisdiction"],
            "insurance_active": record["insurance_active"],
            "primary_physician": record["primary_physician"],
            "last_encounter": record["last_encounter"]
        }
    return {
        "found": False,
        "message": "New patient / unidentified caller. Proceed with identity onboarding."
    }


def verify_patient_pin(phone_number: str, pin: str) -> Dict[str, Any]:
    """
    Verifies caller security PIN or last 4 digits of National ID / SSN
    before revealing Protected Health Information (PHI).
    """
    record = MOCK_PATIENT_DB.get(phone_number)
    if not record:
        return {"verified": False, "error": "Patient record not found"}
    
    if record["security_pin"] == pin:
        return {
            "verified": True,
            "patient_id": record["patient_id"],
            "message": "Identity authenticated successfully. Authorized to access clinical records."
        }
    return {
        "verified": False,
        "error": "Authentication failed. Incorrect PIN/identifier."
    }


def schedule_clinical_appointment(
    phone_number: str,
    specialty: str,
    preferred_time_iso: str
) -> Dict[str, Any]:
    """
    Books an in-person or telemedicine appointment directly into the hospital scheduling system.
    """
    record = MOCK_PATIENT_DB.get(phone_number, {"patient_id": "PT-GUEST-001"})
    booking_id = f"BK-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{record['patient_id'][-4:]}"
    
    logger.info(f"Booked appointment {booking_id} for specialty: {specialty} at {preferred_time_iso}")
    return {
        "booking_id": booking_id,
        "patient_id": record["patient_id"],
        "specialty": specialty,
        "time": preferred_time_iso,
        "status": "CONFIRMED",
        "instructions": "Arrive 15 minutes prior to appointment or join virtual waiting room via SMS link."
    }
