"""
SawtOS Carrier Telephony Finite State Machine (FSM)
Manages the end-to-end call state lifecycle, warm/cold transfers, hold acoustics,
and post-call reconciliation against CPaaS carrier webhooks.
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class CallState(str, Enum):
    IDLE = "IDLE"
    RINGING = "RINGING"
    CONNECTED = "CONNECTED"
    ON_HOLD = "ON_HOLD"
    TRANSFERRING = "TRANSFERRING"
    WRAP_UP = "WRAP_UP"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CallTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class TelephonyCallSession(BaseModel):
    call_sid: str = Field(..., description="Unique CPaaS / Carrier Call SID")
    room_name: str = Field(..., description="Target LiveKit WebRTC room")
    from_number: str = Field(..., description="Caller E.164 phone number")
    to_number: str = Field(..., description="Dialed DID E.164 phone number")
    region: str = Field(default="gulf", description="Geographic jurisdiction (gulf | us)")
    language: str = Field(default="ar-XA", description="Primary spoken language")
    state: CallState = Field(default=CallState.IDLE)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    connected_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    hold_duration_sec: float = 0.0
    transfer_target: Optional[str] = None
    disconnect_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    state_history: List[Dict[str, Any]] = Field(default_factory=list)

    def transition_to(self, new_state: CallState, reason: Optional[str] = None) -> "TelephonyCallSession":
        """Executes a validated state transition with audit logging."""
        valid_transitions = {
            CallState.IDLE: [CallState.RINGING, CallState.FAILED],
            CallState.RINGING: [CallState.CONNECTED, CallState.FAILED, CallState.COMPLETED],
            CallState.CONNECTED: [CallState.ON_HOLD, CallState.TRANSFERRING, CallState.WRAP_UP, CallState.COMPLETED],
            CallState.ON_HOLD: [CallState.CONNECTED, CallState.TRANSFERRING, CallState.WRAP_UP, CallState.COMPLETED],
            CallState.TRANSFERRING: [CallState.CONNECTED, CallState.COMPLETED, CallState.FAILED],
            CallState.WRAP_UP: [CallState.COMPLETED],
            CallState.COMPLETED: [],
            CallState.FAILED: [],
        }

        if new_state not in valid_transitions.get(self.state, []):
            raise CallTransitionError(
                f"Invalid state transition from {self.state} to {new_state} for call {self.call_sid}"
            )

        now = datetime.now(timezone.utc)
        self.state_history.append({
            "from_state": self.state.value,
            "to_state": new_state.value,
            "timestamp": now.isoformat(),
            "reason": reason
        })

        if new_state == CallState.CONNECTED and self.connected_at is None:
            self.connected_at = now
        elif new_state in (CallState.COMPLETED, CallState.FAILED):
            self.ended_at = now
            if reason:
                self.disconnect_reason = reason

        self.state = new_state
        return self

    @property
    def total_duration_seconds(self) -> float:
        if not self.connected_at:
            return 0.0
        end = self.ended_at or datetime.now(timezone.utc)
        return max(0.0, (end - self.connected_at).total_seconds())

    @property
    def billable_minutes(self) -> int:
        """Standard carrier 60-second increment billing calculation."""
        seconds = self.total_duration_seconds
        if seconds <= 0:
            return 0
        return int((seconds + 59) // 60)
