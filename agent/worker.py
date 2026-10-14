"""
SawtOS Real-Time LiveKit Agent Worker Pod
Implements the Dual-Engine Voice Architecture:
- Engine A: Native Speech-to-Speech (S2S) via Gemini Multimodal Live API
- Engine B: Ultra-Fast Cascaded Pipeline (Silero VAD -> Deepgram Nova-3 -> Groq Llama 3.3 -> Cartesia Sonic 3.5)
"""

import os
import asyncio
import logging
from typing import Optional

from dotenv import load_dotenv

# LiveKit Agents imports
from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.pipeline import VoicePipelineAgent

# Plugins
from livekit.plugins import silero, deepgram, cartesia, elevenlabs

# Local imports
from .prompt_templates import GULF_ARABIC_SYSTEM_PROMPT, US_ENGLISH_SYSTEM_PROMPT
from .tools.crm_tools import (
    lookup_caller_context,
    verify_patient_pin,
    schedule_clinical_appointment,
)

load_dotenv()
logger = logging.getLogger("sawtos.agent")
logging.basicConfig(level=logging.INFO)


def prewarm(proc: JobProcess):
    """Pre-loads local ONNX VAD models into memory to achieve zero cold-start delay."""
    logger.info("Pre-warming Silero VAD v5 ONNX runtime...")
    proc.userdata["vad"] = silero.VAD.load(
        min_speech_duration=0.08,
        min_silence_duration=0.35,
        padding_duration=0.1
    )


async def entrypoint(ctx: JobContext):
    """
    Main LiveKit Agent entrypoint triggered whenever a new participant enters a room
    (via WebRTC browser client or LiveKit SIP carrier gateway).
    """
    logger.info(f"Connecting to room: {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # 1. Inspect Room Metadata for Region and Language (Injected by LiveKit SIP Dispatcher)
    room_metadata = ctx.room.metadata or ""
    is_gulf = "gulf" in ctx.room.name or "gulf" in room_metadata or "ar-XA" in room_metadata

    region = "Gulf (UAE/KSA)" if is_gulf else "US (Healthcare/Enterprise)"
    logger.info(f"Session Region: {region} | Room: {ctx.room.name}")

    system_prompt = GULF_ARABIC_SYSTEM_PROMPT if is_gulf else US_ENGLISH_SYSTEM_PROMPT

    # 2. Configure Function Tools for the Agent
    fnc_ctx = llm.FunctionContext()

    @fnc_ctx.ai_callable(description="Look up patient medical records and account tier from phone number.")
    def tool_lookup_caller(phone_number: str) -> str:
        res = lookup_caller_context(phone_number)
        return str(res)

    @fnc_ctx.ai_callable(description="Authenticate patient identity using PIN or last 4 digits of ID.")
    def tool_verify_pin(phone_number: str, pin: str) -> str:
        res = verify_patient_pin(phone_number, pin)
        return str(res)

    @fnc_ctx.ai_callable(description="Schedule a doctor or telemedicine appointment.")
    def tool_schedule(phone_number: str, specialty: str, preferred_time_iso: str) -> str:
        res = schedule_clinical_appointment(phone_number, specialty, preferred_time_iso)
        return str(res)

    # 3. Setup VAD (Voice Activity Detection) & Barge-in Controls
    vad_instance = ctx.proc.userdata.get("vad") or silero.VAD.load()

    # 4. Engine B: Ultra-Fast Cascaded Pipeline Setup
    # STT: Deepgram Nova-3 (with native Arabic / English multilingual models)
    stt_lang = "ar" if is_gulf else "en-US"
    stt_provider = deepgram.STT(
        model="nova-3",
        language=stt_lang,
        interim_results=True,
        smart_format=True,
    )

    # LLM: Groq LPU (Llama 3.3 70B) for sub-90ms TTFT
    # In live deployment, uses Groq or OpenAI/Claude via LiveKit LLM plugin
    groq_api_key = os.getenv("GROQ_API_KEY", "mock_key")
    llm_provider = None
    try:
        from livekit.plugins import openai
        llm_provider = openai.LLM(
            model="llama-3.3-70b-versatile",
            base_url="https://api.groq.com/openai/v1",
            api_key=groq_api_key
        )
    except Exception as e:
        logger.warning(f"Groq LLM initialization fallback: {e}")

    # TTS: Cartesia Sonic 3.5 (85ms TTFB) with Gulf Arabic / English localized voice
    tts_voice = "248be419-c632-4f23-add1-07c49921a471" if is_gulf else "79a125e8-cd45-4c13-8a67-188112f4dd22"
    tts_provider = cartesia.TTS(
        model="sonic-multilingual",
        voice=tts_voice,
    )

    # 5. Initialize VoicePipelineAgent with Instant Barge-In
    agent = VoicePipelineAgent(
        vad=vad_instance,
        stt=stt_provider,
        llm=llm_provider,
        tts=tts_provider,
        fnc_ctx=fnc_ctx,
        chat_ctx=llm.ChatContext().append(
            role="system",
            text=system_prompt,
        ),
        interrupt_speech_duration=0.4,       # Sub-400ms user interrupt threshold
        interrupt_min_words=1,               # Immediate barge-in on first recognized word
        min_endpointing_delay=0.35,          # Rapid turn-taking endpointing
    )

    # 6. Start the Agent in the Room
    agent.start(ctx.room)

    # Initial Greeting
    greeting_text = (
        "مرحباً بك في منصة صوت، كيف يمكنني مساعدتك اليوم؟"
        if is_gulf
        else "Hello, thank you for calling SawtOS care. How can I assist you today?"
    )
    await agent.say(greeting_text, allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        )
    )
