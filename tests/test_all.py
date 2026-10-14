"""
SawtOS Comprehensive Enterprise Test Suite
Validates Telephony FSM, In-Call RAG, Post-Call LLM Judge,
HIPAA Safe Harbor De-identification, and CRM Tool Calling.
"""

import pytest
from telephony.fsm import TelephonyCallSession, CallState, CallTransitionError
from analytics.rag_engine import InCallRAGEngine
from analytics.post_call_judge import PostCallJudge
from healthcare.audit import SafeHarborDeidentifier, HIPAAAuditLogger
from agent.tools.crm_tools import (
    lookup_caller_context,
    verify_patient_pin,
    schedule_clinical_appointment
)


# 1. Telephony Finite State Machine (FSM) Tests
def test_telephony_fsm_valid_lifecycle():
    session = TelephonyCallSession(
        call_sid="CA-test-101",
        room_name="sawt-gulf-101",
        from_number="+966501234567",
        to_number="+966110001111",
        region="gulf",
        state=CallState.IDLE
    )

    # Transition: IDLE -> RINGING -> CONNECTED -> ON_HOLD -> CONNECTED -> WRAP_UP -> COMPLETED
    session.transition_to(CallState.RINGING)
    assert session.state == CallState.RINGING

    session.transition_to(CallState.CONNECTED)
    assert session.state == CallState.CONNECTED
    assert session.connected_at is not None

    session.transition_to(CallState.ON_HOLD)
    assert session.state == CallState.ON_HOLD

    session.transition_to(CallState.CONNECTED)
    assert session.state == CallState.CONNECTED

    session.transition_to(CallState.WRAP_UP)
    assert session.state == CallState.WRAP_UP

    session.transition_to(CallState.COMPLETED, reason="Caller ended conversation")
    assert session.state == CallState.COMPLETED
    assert session.ended_at is not None
    assert len(session.state_history) == 6


def test_telephony_fsm_invalid_transition_fails():
    session = TelephonyCallSession(
        call_sid="CA-test-102",
        room_name="sawt-us-102",
        from_number="+14155552671",
        to_number="+18005550199",
        region="us",
        state=CallState.IDLE
    )

    # Illegal transition: IDLE -> ON_HOLD without connecting first
    with pytest.raises(CallTransitionError):
        session.transition_to(CallState.ON_HOLD)


# 2. In-Call RAG Engine Tests
@pytest.mark.asyncio
async def test_in_call_rag_retrieval():
    engine = InCallRAGEngine()
    
    # Query matching Gulf emergency protocol
    results = await engine.search("Patient has severe chest pain and needs ambulance in Riyadh", top_k=2)
    assert len(results) > 0
    assert "Chest Pain" in results[0].title
    assert results[0].similarity_score > 0.8
    assert results[0].citation is not None


# 3. Post-Call LLM-as-a-Judge QA Scoring Tests
@pytest.mark.asyncio
async def test_post_call_qa_judge_compliant_call():
    judge = PostCallJudge()
    compliant_transcript = (
        "Agent: مرحباً بك في منصة صوت، كيف يمكنني مساعدتك؟\n"
        "Caller: أهلاً، أريد حجز موعد مع دكتور القلب.\n"
        "Agent: أبشر طال عمرك، يرجى تزويدي برمز التحقق لهويتك.\n"
        "Caller: الرمز هو 9988.\n"
        "Agent: تم التحقق بنجاح، وتم حجز الموعد ليوم الأحد الساعة العاشرة صباحاً.\n"
        "Caller: ممتاز جداً، شكراً جزيلاً.\n"
        "Agent: في أمان الله ومع السلامة."
    )

    scorecard = await judge.evaluate_call("CA-eval-001", compliant_transcript, region="gulf")
    assert scorecard.compliance_passed is True
    assert len(scorecard.forbidden_phrases_detected) == 0
    assert scorecard.script_adherence_score >= 75.0
    assert scorecard.csat_score in (4, 5)
    assert scorecard.sentiment_trajectory == "neutral_to_positive"


@pytest.mark.asyncio
async def test_post_call_qa_judge_detects_forbidden_phrase():
    judge = PostCallJudge()
    violating_transcript = (
        "Agent: Hello, I guarantee you will be cured if you take double the dosage.\n"
        "Caller: Are you sure about that?"
    )

    scorecard = await judge.evaluate_call("CA-eval-002", violating_transcript, region="us")
    assert scorecard.compliance_passed is False
    assert len(scorecard.forbidden_phrases_detected) > 0
    assert scorecard.csat_score == 1  # Mandatory compliance failure penalty


# 4. HIPAA Safe Harbor De-identification & Audit Tests
def test_hipaa_safe_harbor_scrubbing():
    dirty_text = "Patient John Connor (+1-415-555-2671), SSN 123-45-6789, born on May 12, 1984, email jconnor@skynet.org"
    scrubbed = SafeHarborDeidentifier.scrub_phi(dirty_text)

    assert scrubbed["is_safe_harbor_compliant"] is True
    assert "+1-415-555-2671" not in scrubbed["sanitized_text"]
    assert "123-45-6789" not in scrubbed["sanitized_text"]
    assert "jconnor@skynet.org" not in scrubbed["sanitized_text"]
    assert "[REDACTED_PHONE]" in scrubbed["sanitized_text"]
    assert "[REDACTED_ID]" in scrubbed["sanitized_text"]


def test_hipaa_audit_logger_generates_hmac():
    evt = HIPAAAuditLogger.log_phi_access(
        actor_id="dr_silberman",
        action_type="READ_PHI",
        patient_id="PT-90210",
        resource="electronic_health_record"
    )

    assert evt.event_id.startswith("evt-")
    assert len(evt.tamper_proof_hash) == 64  # SHA-256 length


# 5. CRM Tool Calling Tests
def test_crm_tool_caller_lookup_and_booking():
    # US patient lookup
    us_patient = lookup_caller_context("+14155552671")
    assert us_patient["found"] is True
    assert us_patient["name"] == "Sarah Connor"

    # PIN Verification
    pin_fail = verify_patient_pin("+14155552671", "0000")
    assert pin_fail["verified"] is False

    pin_ok = verify_patient_pin("+14155552671", "1984")
    assert pin_ok["verified"] is True

    # Appointment booking
    booking = schedule_clinical_appointment("+14155552671", "Cardiology", "2026-10-25T10:00:00Z")
    assert booking["status"] == "CONFIRMED"
    assert booking["booking_id"].startswith("BK-")
