'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Phone,
  PhoneCall,
  PhoneOff,
  Mic,
  MicOff,
  Volume2,
  Pause,
  Play,
  ArrowRightLeft,
  Activity,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Globe,
  Sparkles,
  BarChart3,
  FileText,
  Clock,
  Terminal,
  Server
} from 'lucide-react';

type CallState = 'IDLE' | 'RINGING' | 'CONNECTED' | 'ON_HOLD' | 'TRANSFERRING' | 'WRAP_UP';

interface TranscriptLine {
  speaker: 'agent' | 'caller';
  text: string;
  translation?: string;
  timestamp: string;
}

export default function SawtOSConsole() {
  const [callState, setCallState] = useState<CallState>('IDLE');
  const [region, setRegion] = useState<'gulf' | 'us'>('gulf');
  const [phoneNumber, setPhoneNumber] = useState('+966 50 123 4567');
  const [isMuted, setIsMuted] = useState(false);
  const [callSeconds, setCallSeconds] = useState(0);
  const [showQAModal, setShowQAModal] = useState(false);
  
  // Transcripts
  const [transcripts, setTranscripts] = useState<TranscriptLine[]>([
    {
      speaker: 'agent',
      text: 'مرحباً بك في منصة صوت الذكية، كيف يمكنني مساعدتك اليوم؟',
      translation: 'Hello and welcome to SawtOS Smart Voice care. How may I assist you today?',
      timestamp: '00:02'
    },
    {
      speaker: 'caller',
      text: 'يا هلا، بغيت استفسر عن موعدي القادم مع الدكتور طارق الغامدي في عيادة الباطنية.',
      translation: 'Hello, I would like to inquire about my upcoming appointment with Dr. Tariq Al-Ghamdi in Internal Medicine.',
      timestamp: '00:07'
    },
    {
      speaker: 'agent',
      text: 'أبشر طال عمرك، يرجى تزويدي برمز التحقق لهويتك للتأكد من الملف الطبي.',
      translation: 'Certainly! Please provide your identity security PIN to verify your medical record.',
      timestamp: '00:11'
    }
  ]);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Timer effect
  useEffect(() => {
    let interval: any;
    if (callState === 'CONNECTED' || callState === 'ON_HOLD') {
      interval = setInterval(() => {
        setCallSeconds((s) => s + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [callState]);

  // Audio Canvas Waveform simulation
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;
    let phase = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const isSpeaking = callState === 'CONNECTED';
      const waveColor = isSpeaking ? '#10b981' : '#334155';

      ctx.beginPath();
      ctx.lineWidth = 2.5;
      ctx.strokeStyle = waveColor;

      const centerY = canvas.height / 2;
      for (let x = 0; x < canvas.width; x++) {
        const amplitude = isSpeaking ? 18 * Math.sin((x * 0.04) + phase) : 3;
        const y = centerY + amplitude * Math.sin((x * 0.02) + phase);
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      phase += isSpeaking ? 0.08 : 0.01;
      animationId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animationId);
  }, [callState]);

  const startInboundCall = () => {
    setCallState('RINGING');
    setCallSeconds(0);
    setTimeout(() => {
      setCallState('CONNECTED');
    }, 2000);
  };

  const endCall = () => {
    setCallState('WRAP_UP');
    setTimeout(() => {
      setCallState('IDLE');
      setShowQAModal(true);
    }, 1200);
  };

  const toggleHold = () => {
    if (callState === 'CONNECTED') setCallState('ON_HOLD');
    else if (callState === 'ON_HOLD') setCallState('CONNECTED');
  };

  const formatDuration = (secs: number) => {
    const m = Math.floor(secs / 60).toString().padStart(2, '0');
    const s = (secs % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  return (
    <div className="min-h-screen bg-[#070b12] text-slate-100 p-4 md:p-6 flex flex-col font-sans">
      {/* Top Enterprise Navigation Bar */}
      <header className="flex flex-wrap items-center justify-between border-b border-slate-800/80 pb-4 mb-6 gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-emerald-500/20 font-bold text-black text-xl">
            ص
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white">SawtOS</h1>
              <span className="px-2 py-0.5 text-xs font-semibold rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                LiveKit SIP v1.1
              </span>
            </div>
            <p className="text-xs text-slate-400">Carrier-Grade Real-Time Voice & Telephony Engine</p>
          </div>
        </div>

        {/* Region & Engine Selector */}
        <div className="flex items-center gap-3">
          <div className="flex bg-slate-900 border border-slate-800 rounded-lg p-1">
            <button
              onClick={() => { setRegion('gulf'); setPhoneNumber('+966 50 123 4567'); }}
              className={`px-3 py-1.5 text-xs font-medium rounded-md flex items-center gap-1.5 transition-all ${
                region === 'gulf' ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              <Globe className="w-3.5 h-3.5" />
              Gulf (UAE / KSA)
            </button>
            <button
              onClick={() => { setRegion('us'); setPhoneNumber('+1 (415) 555-2671'); }}
              className={`px-3 py-1.5 text-xs font-medium rounded-md flex items-center gap-1.5 transition-all ${
                region === 'us' ? 'bg-cyan-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              US Healthcare (HIPAA)
            </button>
          </div>

          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Twilio SIP Trunk: Active
          </div>
        </div>
      </header>

      {/* Main Grid: Softphone Dialpad & Live Operations */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1">
        
        {/* Left Column: Virtual Carrier Softphone (4 Cols) */}
        <div className="lg:col-span-4 bg-[#0d131f] border border-slate-800/90 rounded-2xl p-5 flex flex-col justify-between shadow-2xl">
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <PhoneCall className="w-3.5 h-3.5 text-emerald-400" />
                Virtual Softphone HUD
              </span>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                callState === 'CONNECTED' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
                callState === 'RINGING' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30 animate-pulse' :
                callState === 'ON_HOLD' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' :
                'bg-slate-800 text-slate-400'
              }`}>
                {callState}
              </span>
            </div>

            {/* Caller ID Screen */}
            <div className="bg-[#080d16] border border-slate-800 rounded-xl p-4 text-center mb-5">
              <p className="text-xs text-slate-400 mb-1">
                {region === 'gulf' ? 'KSA Inbound SIP Carrier (Mobily/STC)' : 'US Toll-Free Inbound (Twilio PSTN)'}
              </p>
              <input
                type="text"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                className="bg-transparent text-xl font-mono text-center font-bold text-white tracking-wider outline-none w-full"
              />
              <p className="text-xs text-emerald-400 font-mono mt-1 flex items-center justify-center gap-1">
                <Clock className="w-3 h-3" />
                {formatDuration(callSeconds)}
              </p>
            </div>

            {/* Dialpad Matrix */}
            <div className="grid grid-cols-3 gap-2.5 mb-6">
              {['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#'].map((digit) => (
                <button
                  key={digit}
                  onClick={() => setPhoneNumber((prev) => prev + digit)}
                  className="py-3 bg-slate-900/90 hover:bg-slate-800 border border-slate-800 rounded-xl text-lg font-semibold text-slate-200 transition-colors shadow-sm"
                >
                  {digit}
                </button>
              ))}
            </div>
          </div>

          {/* Telephony Action Bar */}
          <div className="space-y-3 pt-3 border-t border-slate-800">
            {callState === 'IDLE' ? (
              <button
                onClick={startInboundCall}
                className="w-full py-3.5 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-slate-950 font-bold rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/25 transition-all text-sm"
              >
                <Phone className="w-4 h-4 fill-current" />
                Simulate Carrier Inbound Call
              </button>
            ) : (
              <div className="space-y-2">
                <div className="grid grid-cols-3 gap-2">
                  <button
                    onClick={() => setIsMuted(!isMuted)}
                    className={`py-2.5 rounded-xl border text-xs font-semibold flex flex-col items-center gap-1 transition-all ${
                      isMuted ? 'bg-red-500/20 text-red-300 border-red-500/30' : 'bg-slate-900 text-slate-300 border-slate-800 hover:bg-slate-800'
                    }`}
                  >
                    {isMuted ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                    {isMuted ? 'Muted' : 'Mute'}
                  </button>

                  <button
                    onClick={toggleHold}
                    className={`py-2.5 rounded-xl border text-xs font-semibold flex flex-col items-center gap-1 transition-all ${
                      callState === 'ON_HOLD' ? 'bg-purple-500/20 text-purple-300 border-purple-500/30' : 'bg-slate-900 text-slate-300 border-slate-800 hover:bg-slate-800'
                    }`}
                  >
                    {callState === 'ON_HOLD' ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
                    {callState === 'ON_HOLD' ? 'Resume' : 'Hold'}
                  </button>

                  <button
                    onClick={() => alert('Warm transfer executed: Routing to Tier-2 Clinical Lead.')}
                    className="py-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded-xl text-xs font-semibold flex flex-col items-center gap-1 transition-all"
                  >
                    <ArrowRightLeft className="w-4 h-4 text-cyan-400" />
                    Transfer
                  </button>
                </div>

                <button
                  onClick={endCall}
                  className="w-full py-3 bg-red-600 hover:bg-red-500 text-white font-bold rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-red-500/20 transition-all text-sm"
                >
                  <PhoneOff className="w-4 h-4" />
                  Terminate Call & Trigger QA Judge
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Audio Waveform, Live Dual-Language Transcript & Waterfall (8 Cols) */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          
          {/* Reactive Waveform & Latency Waterfall Banner */}
          <div className="bg-[#0d131f] border border-slate-800/90 rounded-2xl p-5 shadow-2xl">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-cyan-400" />
                Acoustic Waveform & Turn-Taking Interruption (Barge-In)
              </span>
              <span className="text-xs font-mono text-slate-400">Silero VAD ONNX: 1.2ms</span>
            </div>

            {/* Canvas Waveform */}
            <div className="h-16 w-full bg-[#080d16] border border-slate-800 rounded-xl overflow-hidden flex items-center justify-center mb-4">
              <canvas ref={canvasRef} width={600} height={64} className="w-full h-full" />
            </div>

            {/* Sub-300ms Waterfall SLA */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-2 border-t border-slate-800/80 text-center">
              <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800">
                <p className="text-[10px] text-slate-400 uppercase font-semibold">Silero VAD</p>
                <p className="text-xs font-mono font-bold text-emerald-400">1.2 ms</p>
              </div>
              <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800">
                <p className="text-[10px] text-slate-400 uppercase font-semibold">Deepgram Nova-3</p>
                <p className="text-xs font-mono font-bold text-cyan-400">118 ms</p>
              </div>
              <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800">
                <p className="text-[10px] text-slate-400 uppercase font-semibold">Groq Llama 3.3</p>
                <p className="text-xs font-mono font-bold text-purple-400">82 ms (TTFT)</p>
              </div>
              <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800">
                <p className="text-[10px] text-slate-400 uppercase font-semibold">Cartesia Sonic</p>
                <p className="text-xs font-mono font-bold text-amber-400">84 ms (TTFB)</p>
              </div>
              <div className="col-span-2 sm:col-span-1 bg-emerald-500/10 p-2 rounded-lg border border-emerald-500/30">
                <p className="text-[10px] text-emerald-300 uppercase font-bold">Total E2E</p>
                <p className="text-xs font-mono font-extrabold text-emerald-400">285.2 ms SLA</p>
              </div>
            </div>
          </div>

          {/* Live Dual-Language Transcript Stream */}
          <div className="bg-[#0d131f] border border-slate-800/90 rounded-2xl p-5 flex-1 flex flex-col shadow-2xl">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-emerald-400" />
                <h2 className="text-sm font-bold text-white">Live Conversational Stream & Acoustic Grounding</h2>
              </div>
              <span className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                Sub-4ms pgvector RAG Grounded
              </span>
            </div>

            {/* Transcript Bubbles */}
            <div className="space-y-3.5 flex-1 overflow-y-auto max-h-[340px] pr-2">
              {transcripts.map((t, idx) => (
                <div
                  key={idx}
                  className={`flex flex-col ${
                    t.speaker === 'agent' ? 'items-start' : 'items-end'
                  }`}
                >
                  <div className="flex items-center gap-1.5 mb-1 text-[11px] text-slate-400">
                    <span className="font-semibold text-slate-300">
                      {t.speaker === 'agent' ? 'SawtOS Voice Agent' : 'Caller (+966 50...)'}
                    </span>
                    <span>• {t.timestamp}</span>
                  </div>
                  <div
                    className={`max-w-[85%] p-3.5 rounded-2xl text-xs leading-relaxed ${
                      t.speaker === 'agent'
                        ? 'bg-slate-900/90 border border-slate-800 text-slate-100 rounded-tl-sm'
                        : 'bg-emerald-600/15 border border-emerald-500/30 text-emerald-100 rounded-tr-sm'
                    }`}
                  >
                    <p className="font-medium mb-1.5 text-slate-100">{t.text}</p>
                    {t.translation && (
                      <p className="text-[11px] text-slate-400 border-t border-slate-800/80 pt-1.5 mt-1 italic">
                        {t.translation}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Post-Call LLM-as-a-Judge QA Modal */}
      {showQAModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#0f172a] border border-slate-700/80 rounded-2xl max-w-xl w-full p-6 shadow-2xl relative animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-5">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-bold">
                  ✓
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Post-Call LLM-as-a-Judge QA Audit</h3>
                  <p className="text-xs text-slate-400">Call SID: CA-99214 • Langfuse Traced</p>
                </div>
              </div>
              <button
                onClick={() => setShowQAModal(false)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              {/* Scorecard Overview */}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800 text-center">
                  <p className="text-[10px] text-slate-400 uppercase font-semibold">Predicted CSAT</p>
                  <p className="text-xl font-bold text-emerald-400 mt-1">5.0 / 5.0</p>
                </div>
                <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800 text-center">
                  <p className="text-[10px] text-slate-400 uppercase font-semibold">Script Adherence</p>
                  <p className="text-xl font-bold text-cyan-400 mt-1">96.5%</p>
                </div>
                <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800 text-center">
                  <p className="text-[10px] text-slate-400 uppercase font-semibold">Compliance Status</p>
                  <p className="text-sm font-bold text-emerald-400 mt-2 flex items-center justify-center gap-1">
                    <CheckCircle2 className="w-4 h-4" /> 100% Passed
                  </p>
                </div>
              </div>

              {/* Sentiment Trajectory */}
              <div className="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800">
                <p className="text-xs font-semibold text-slate-300 mb-1">Sentiment Progression:</p>
                <div className="flex items-center gap-2 text-xs">
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300">Neutral (Opening)</span>
                  <span className="text-slate-500">→</span>
                  <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-semibold">Positive (Resolution)</span>
                </div>
              </div>

              {/* HIPAA / Regional Audit Vault Proof */}
              <div className="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800">
                <p className="text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  HIPAA Safe Harbor & Cryptographic HMAC Stamp
                </p>
                <p className="text-[11px] font-mono text-slate-400 break-all bg-slate-950 p-2 rounded border border-slate-800/80">
                  SHA-256 HMAC: a8f9c10d8e244b7f9910c2830e94998124da... (Tamper Evident)
                </p>
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setShowQAModal(false)}
                className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold rounded-xl text-xs transition-colors"
              >
                Close Audit Report
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
