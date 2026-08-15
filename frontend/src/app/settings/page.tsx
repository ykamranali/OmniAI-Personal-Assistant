"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  Settings,
  Bot,
  Mic,
  Volume2,
  ShieldCheck,
  RefreshCw,
  Check,
  AlertTriangle,
  Radio,
  ArrowLeft,
} from "lucide-react";

type OllamaModel = {
  name: string;
  size?: number;
};

type RuntimeSettings = {
  default_model: string;
  voice_enabled: boolean;
  tts_voice: string;
  os_control_allowed: boolean;
  os_agent_vision_model: string;
  os_agent_max_steps: number;
  os_agent_timeout_seconds: number;
  voice_loop_enabled: boolean;
  wake_word: string;
  voice_barge_in_enabled: boolean;
};

type Voice = {
  id: string;
  name: string;
  language: string;
};

const cardClass =
  "glass rounded-xl p-6 text-white border border-white/5";

export default function SettingsPage() {
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [voices, setVoices] = useState<Voice[]>([]);
  const [runtimeSettings, setRuntimeSettings] = useState<RuntimeSettings>({
    default_model: "llama3.2:3b",
    voice_enabled: false,
    tts_voice: "en-US-AriaNeural",
    os_control_allowed: false,
    os_agent_vision_model: "llama3.2-vision",
    os_agent_max_steps: 25,
    os_agent_timeout_seconds: 240,
    voice_loop_enabled: false,
    wake_word: "hey_jarvis",
    voice_barge_in_enabled: true,
  });
  const [loadingModels, setLoadingModels] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<"idle" | "success" | "error">("idle");
  const [saveError, setSaveError] = useState<string | null>(null);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [voiceLoopRunning, setVoiceLoopRunning] = useState(false);

  // ── Fetch initial data ────────────────────────────────────────────────────
  useEffect(() => {
    const init = async () => {
      try {
        const [settingsRes, modelsRes, voicesRes] = await Promise.all([
          fetch("http://127.0.0.1:8000/api/v1/system/settings"),
          fetch("http://127.0.0.1:8000/api/v1/models/"),
          fetch("http://127.0.0.1:8000/api/v1/voice/voices"),
        ]);

        if (settingsRes.ok) {
          const d = await settingsRes.json();
          if (d.status === "success") setRuntimeSettings(d.data);
        }
        if (modelsRes.ok) {
          const d = await modelsRes.json();
          if (d.status === "success") setModels(d.data);
        }
        if (voicesRes.ok) {
          const d = await voicesRes.json();
          if (d.status === "success") setVoices(d.data);
        }

        try {
          const loopRes = await fetch("http://127.0.0.1:8000/api/v1/voice/loop/status");
          if (loopRes.ok) {
            const d = await loopRes.json();
            if (d.status === "success") setVoiceLoopRunning(d.data.running);
          }
        } catch {
          // ignore — status pill just won't update
        }

        setBackendOnline(true);
      } catch {
        setBackendOnline(false);
      } finally {
        setLoadingModels(false);
      }
    };
    init();
  }, []);

  // ── Save settings ─────────────────────────────────────────────────────────
  const handleSave = async () => {
    setSaving(true);
    setSaveStatus("idle");
    setSaveError(null);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/system/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(runtimeSettings),
      });
      if (!res.ok) throw new Error("Server error");
      const d = await res.json();
      if (d.status === "error") {
        // e.g. the voice loop failed to start (missing mic/dependency) — revert the toggle
        setSaveError(d.message || "Failed to apply setting");
        setRuntimeSettings((s) => ({ ...s, voice_loop_enabled: false }));
        setVoiceLoopRunning(false);
        setSaveStatus("error");
      } else {
        setVoiceLoopRunning(runtimeSettings.voice_loop_enabled);
        setSaveStatus("success");
      }
    } catch {
      setSaveStatus("error");
    } finally {
      setSaving(false);
      setTimeout(() => setSaveStatus("idle"), 4000);
    }
  };

  const fmt = (bytes: number) =>
    bytes ? `${(bytes / 1e9).toFixed(1)} GB` : "";

  return (
    <div className="min-h-screen p-8 text-white relative overflow-hidden">
      {/* Background orbs */}
      <div className="absolute top-[-5%] right-[-5%] w-[35%] h-[35%] rounded-full bg-purple-700/15 blur-[100px] pointer-events-none" />
      <div className="absolute bottom-[-5%] left-[-5%] w-[35%] h-[35%] rounded-full bg-blue-700/15 blur-[100px] pointer-events-none" />

      <header className="flex justify-between items-center mb-10 relative z-10">
        <div>
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-sm text-gray-400 hover:text-white transition mb-3"
          >
            <ArrowLeft size={16} /> Back to chat
          </Link>
          <div className="flex items-center gap-3">
            <Settings className="text-purple-400" size={28} />
            <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
              Settings
            </h1>
          </div>
          <p className="text-gray-400 mt-1 ml-1">Configure OmniAI runtime behaviour</p>
        </div>

        {/* Backend status badge */}
        <div
          className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium border ${
            backendOnline === null
              ? "border-gray-600 text-gray-400"
              : backendOnline
              ? "border-green-500/40 text-green-400 bg-green-500/10"
              : "border-red-500/40 text-red-400 bg-red-500/10"
          }`}
        >
          <div
            className={`h-2 w-2 rounded-full ${
              backendOnline === null
                ? "bg-gray-400"
                : backendOnline
                ? "bg-green-400 animate-pulse"
                : "bg-red-400"
            }`}
          />
          {backendOnline === null
            ? "Connecting..."
            : backendOnline
            ? "Backend Online"
            : "Backend Offline"}
        </div>
      </header>

      {!backendOnline && backendOnline !== null && (
        <div className="mb-6 flex items-center gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 text-sm">
          <AlertTriangle size={18} />
          Cannot reach the backend at <code className="font-mono">http://127.0.0.1:8000</code>.
          Make sure the FastAPI server is running.
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 relative z-10">



        {/* ── Voice Input ────────────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className={cardClass}
        >
          <div className="flex items-center gap-2 mb-6">
            <Mic className="text-blue-400" size={20} />
            <h2 className="text-xl font-semibold">Voice Input (STT)</h2>
          </div>

          <div className="flex items-center justify-between mb-6">
            <div>
              <p className="font-medium">Enable Voice Input</p>
              <p className="text-sm text-gray-400 mt-0.5">
                Uses the browser's built-in Speech Recognition API
              </p>
            </div>
            <button
              onClick={() =>
                setRuntimeSettings((s) => ({ ...s, voice_enabled: !s.voice_enabled }))
              }
              className={`relative inline-flex h-7 w-12 items-center rounded-full transition-colors focus:outline-none ${
                runtimeSettings.voice_enabled ? "bg-blue-500" : "bg-white/10"
              }`}
            >
              <span
                className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${
                  runtimeSettings.voice_enabled ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
          </div>

          <div
            className={`p-3 rounded-lg border text-sm ${
              runtimeSettings.voice_enabled
                ? "bg-blue-500/10 border-blue-500/20 text-blue-300"
                : "bg-white/3 border-white/5 text-gray-500"
            }`}
          >
            {runtimeSettings.voice_enabled
              ? "🎙️ Voice input is enabled. A microphone button will appear in the chat interface."
              : "Voice input is disabled. Enable it to speak to OmniAI."}
          </div>
        </motion.div>

        {/* ── TTS Voice ─────────────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className={cardClass}
        >
          <div className="flex items-center gap-2 mb-6">
            <Volume2 className="text-pink-400" size={20} />
            <h2 className="text-xl font-semibold">Text-to-Speech</h2>
          </div>

          <label className="block text-sm text-gray-400 mb-2">TTS Voice</label>
          <select
            value={runtimeSettings.tts_voice}
            onChange={(e) =>
              setRuntimeSettings((s) => ({ ...s, tts_voice: e.target.value }))
            }
            className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-pink-500 appearance-none cursor-pointer"
          >
            {voices.map((v) => (
              <option key={v.id} value={v.id} className="bg-zinc-900">
                {v.name}
              </option>
            ))}
          </select>

          <p className="mt-4 text-xs text-gray-500">
            Powered by <span className="text-gray-300">Microsoft Edge TTS</span>. Voices require
            an internet connection.
          </p>
        </motion.div>

        {/* ── OS Control ────────────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className={cardClass}
        >
          <div className="flex items-center gap-2 mb-6">
            <ShieldCheck className="text-orange-400" size={20} />
            <h2 className="text-xl font-semibold">OS Control</h2>
          </div>

          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="font-medium">Allow OS Automation</p>
              <p className="text-sm text-gray-400 mt-0.5">
                Lets the AI launch apps, type, and take screenshots
              </p>
            </div>
            <button
              onClick={() =>
                setRuntimeSettings((s) => ({
                  ...s,
                  os_control_allowed: !s.os_control_allowed,
                }))
              }
              className={`relative inline-flex h-7 w-12 items-center rounded-full transition-colors focus:outline-none ${
                runtimeSettings.os_control_allowed ? "bg-orange-500" : "bg-white/10"
              }`}
            >
              <span
                className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${
                  runtimeSettings.os_control_allowed ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
          </div>

          <div
            className={`p-3 rounded-lg border text-sm ${
              runtimeSettings.os_control_allowed
                ? "bg-orange-500/10 border-orange-500/20 text-orange-300"
                : "bg-white/3 border-white/5 text-gray-500"
            }`}
          >
            {runtimeSettings.os_control_allowed ? (
              <>
                ⚠️ <strong>OS Control is ON.</strong> The AI can automate your desktop. Use with
                caution — only ask it to do things you trust.
              </>
            ) : (
              "OS Control is OFF. The AI cannot access your desktop."
            )}
          </div>

          <div className="mt-5 space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">
                Vision model (must be a vision-capable Ollama model)
              </label>
              <input
                type="text"
                value={runtimeSettings.os_agent_vision_model}
                onChange={(e) =>
                  setRuntimeSettings((s) => ({ ...s, os_agent_vision_model: e.target.value }))
                }
                placeholder="llama3.2-vision"
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
              <p className="mt-1.5 text-xs text-gray-500">
                Screenshots are sent to this model each step. A text-only model (like the default
                chat model) can&apos;t see the screen — run <code className="font-mono">ollama pull llama3.2-vision</code> first.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Max steps</label>
                <input
                  type="number"
                  min={1}
                  max={100}
                  value={runtimeSettings.os_agent_max_steps}
                  onChange={(e) =>
                    setRuntimeSettings((s) => ({ ...s, os_agent_max_steps: Number(e.target.value) }))
                  }
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Timeout (seconds)</label>
                <input
                  type="number"
                  min={30}
                  max={1800}
                  value={runtimeSettings.os_agent_timeout_seconds}
                  onChange={(e) =>
                    setRuntimeSettings((s) => ({ ...s, os_agent_timeout_seconds: Number(e.target.value) }))
                  }
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
              </div>
            </div>
            <p className="text-xs text-gray-500">
              Requests that look sensitive (deleting things, sending messages, spending money,
              handling passwords) will pause in chat and ask you to approve before proceeding.
            </p>
          </div>
        </motion.div>

        {/* ── Always-on Voice Assistant ─────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className={cardClass}
        >
          <div className="flex items-center gap-2 mb-6">
            <Radio className="text-green-400" size={20} />
            <h2 className="text-xl font-semibold">Always-On Voice Assistant</h2>
          </div>

          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="font-medium">Hands-free wake word listening</p>
              <p className="text-sm text-gray-400 mt-0.5">
                Runs fully locally: say the wake word, then talk — no clicking a mic button.
                Requires a working microphone/speakers on the machine running the backend.
              </p>
            </div>
            <button
              onClick={() =>
                setRuntimeSettings((s) => ({ ...s, voice_loop_enabled: !s.voice_loop_enabled }))
              }
              className={`relative inline-flex h-7 w-12 items-center rounded-full transition-colors focus:outline-none shrink-0 ml-4 ${
                runtimeSettings.voice_loop_enabled ? "bg-green-500" : "bg-white/10"
              }`}
            >
              <span
                className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${
                  runtimeSettings.voice_loop_enabled ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
          </div>

          <div className="mb-4">
            <label className="block text-sm text-gray-400 mb-2">Wake word</label>
            <select
              value={runtimeSettings.wake_word}
              onChange={(e) => setRuntimeSettings((s) => ({ ...s, wake_word: e.target.value }))}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-green-500 appearance-none cursor-pointer"
            >
              <option value="hey_jarvis" className="bg-zinc-900">Hey Jarvis</option>
              <option value="alexa" className="bg-zinc-900">Alexa</option>
              <option value="hey_mycroft" className="bg-zinc-900">Hey Mycroft</option>
            </select>
          </div>

          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="font-medium text-sm">Allow interrupting while it talks</p>
              <p className="text-xs text-gray-500 mt-0.5">Barge-in: start speaking to cut off playback</p>
            </div>
            <button
              onClick={() =>
                setRuntimeSettings((s) => ({ ...s, voice_barge_in_enabled: !s.voice_barge_in_enabled }))
              }
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none shrink-0 ${
                runtimeSettings.voice_barge_in_enabled ? "bg-green-500" : "bg-white/10"
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                  runtimeSettings.voice_barge_in_enabled ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
          </div>

          <div
            className={`p-3 rounded-lg border text-sm flex items-center gap-2 ${
              voiceLoopRunning
                ? "bg-green-500/10 border-green-500/20 text-green-300"
                : "bg-white/3 border-white/5 text-gray-500"
            }`}
          >
            <div className={`h-2 w-2 rounded-full ${voiceLoopRunning ? "bg-green-400 animate-pulse" : "bg-gray-500"}`} />
            {voiceLoopRunning ? "Listening in the background." : "Not running."} Toggle and click
            Save Settings to apply.
          </div>
        </motion.div>
      </div>

      {/* ── Save Button ──────────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="mt-8 flex justify-end items-center gap-4 relative z-10"
      >
        {saveStatus === "success" && (
          <span className="flex items-center gap-2 text-green-400 text-sm">
            <Check size={16} /> Settings saved!
          </span>
        )}
        {saveStatus === "error" && (
          <span className="flex items-center gap-2 text-red-400 text-sm max-w-md text-right">
            <AlertTriangle size={16} className="shrink-0" />
            {saveError || "Failed to save. Is the backend running?"}
          </span>
        )}
        <button
          onClick={handleSave}
          disabled={saving || !backendOnline}
          className="flex items-center gap-2 px-8 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 disabled:opacity-50 text-white font-semibold rounded-xl transition-all duration-200 shadow-lg shadow-purple-500/20"
        >
          {saving ? (
            <RefreshCw size={18} className="animate-spin" />
          ) : (
            <Check size={18} />
          )}
          {saving ? "Saving…" : "Save Settings"}
        </button>
      </motion.div>
    </div>
  );
}
