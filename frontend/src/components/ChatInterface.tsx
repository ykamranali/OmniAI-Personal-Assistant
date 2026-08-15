"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import {
  Send,
  Bot,
  User,
  Database,
  Mic,
  MicOff,
  ChevronDown,
  ShieldCheck,
  ShieldOff,
  RefreshCw,
  Square,
} from "lucide-react";

type Message = {
  role: "user" | "assistant";
  content: string;
};

type OllamaModel = {
  name: string;
};

// ── Web Speech API types (not in default TS lib) ─────────────────────────────
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type SpeechRecognitionConstructor = new () => any;

declare global {
  interface Window {
    SpeechRecognition: SpeechRecognitionConstructor;
    webkitSpeechRecognition: SpeechRecognitionConstructor;
  }
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Hello! I am OmniAI. How can I assist you today?" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [memoryConfirmation, setMemoryConfirmation] = useState<{
    fact: string;
    collection: string;
  } | null>(null);
  const [osConfirmation, setOsConfirmation] = useState<{
    request: string;
  } | null>(null);

  // ── Always-on voice loop status (pushed over the /ws socket) ───────────────
  const [voiceLoopState, setVoiceLoopState] = useState<
    "idle" | "listening" | "thinking" | "speaking" | "stopped" | null
  >(null);

  // ── Model selector ────────────────────────────────────────────────────────
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [selectedModel, setSelectedModel] = useState("llama3.2:3b");
  const [loadingModels, setLoadingModels] = useState(true);

  // ── OS control ────────────────────────────────────────────────────────────
  const [osControlAllowed, setOsControlAllowed] = useState(false);

  // ── Voice input ───────────────────────────────────────────────────────────
  const [isListening, setIsListening] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognitionRef = useRef<any>(null);

  const bottomRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const [ttsUrl, setTtsUrl] = useState<string | null>(null);

  const inputRef = useRef(input);
  useEffect(() => { inputRef.current = input; }, [input]);

  const handleSendRef = useRef<any>(null);

  const playTTS = async (text: string) => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/system/settings");
      const data = await res.json();
      if (data.status === "success" && data.data.voice_enabled) {
        const ttsRes = await fetch("http://127.0.0.1:8000/api/v1/voice/synthesize", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text, voice: data.data.tts_voice || "en-US-AriaNeural" })
        });
        if (ttsRes.ok) {
          const blob = await ttsRes.blob();
          const url = URL.createObjectURL(blob);
          setTtsUrl(url);
        }
      }
    } catch (e) {
      console.error("TTS error", e);
    }
  };

  // ── Check voice support ───────────────────────────────────────────────────
  useEffect(() => {
    if (
      typeof window !== "undefined" &&
      ("SpeechRecognition" in window || "webkitSpeechRecognition" in window)
    ) {
      setTimeout(() => setVoiceSupported(true), 0);
    }
  }, []);

  // ── Fetch models ─────────────────────────────────────────────────────────
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/v1/models/");
        const data = await res.json();
        if (data.status === "success" && data.data.length > 0) {
          setModels(data.data);
          setSelectedModel(data.data[0].name);
        }
      } catch {
        // Keep default model name
      } finally {
        setLoadingModels(false);
      }
    };
    fetchModels();
  }, []);

  // ── Fetch runtime settings (default model, OS control) ───────────────────
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/v1/system/settings");
        const data = await res.json();
        if (data.status === "success") {
          if (data.data.default_model) setSelectedModel(data.data.default_model);
          if (typeof data.data.os_control_allowed === "boolean") {
            setOsControlAllowed(data.data.os_control_allowed);
          }
        }
      } catch {
        // ignore
      }
    };
    fetchSettings();
  }, []);

  // ── WebSocket for OS control config broadcast + voice-loop status push ─────
  useEffect(() => {
    const ws = new WebSocket("ws://127.0.0.1:8000/ws");
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({ type: "config", os_control_allowed: osControlAllowed }));
    };

    ws.onmessage = (event) => {
      let msg: any; // eslint-disable-line @typescript-eslint/no-explicit-any
      try {
        msg = JSON.parse(event.data);
      } catch {
        return;
      }

      switch (msg.type) {
        case "voice_loop_state":
          setVoiceLoopState(msg.state);
          break;
        case "voice_loop_transcript":
          setMessages((prev) => [...prev, { role: "user", content: msg.text }]);
          break;
        case "voice_loop_reply":
          setMessages((prev) => [...prev, { role: "assistant", content: msg.text }]);
          break;
        case "voice_loop_error":
          console.error("Voice loop error:", msg.message);
          break;
        default:
          // system_stats and other broadcasts aren't handled by this component
          break;
      }
    };

    return () => ws.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Broadcast OS control changes over the existing WS
  useEffect(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({ type: "config", os_control_allowed: osControlAllowed })
      );
    }
  }, [osControlAllowed]);

  // ── Auto-scroll ───────────────────────────────────────────────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, memoryConfirmation]);

  // ── Voice recognition ─────────────────────────────────────────────────────
  const startListening = useCallback(() => {
    const SpeechRecognitionAPI =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognitionAPI) return;

    const recognition = new SpeechRecognitionAPI();
    recognition.lang = "en-US";
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    recognition.onresult = (event: any) => {
      let finalStr = "";
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalStr += event.results[i][0].transcript;
        }
      }
      if (finalStr) {
        const newText = inputRef.current + (inputRef.current && !inputRef.current.endsWith(" ") ? " " : "") + finalStr.trim();
        setInput(newText);
        inputRef.current = newText;
      }
    };
    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => {
      setIsListening(false);
      if (inputRef.current.trim() && handleSendRef.current) {
        handleSendRef.current(inputRef.current);
      }
    };

    recognitionRef.current = recognition;
    recognition.start();
    setIsListening(true);
  }, []);

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop();
    // onend will handle the state update and auto-sending
  }, []);

  // ── Send message ──────────────────────────────────────────────────────────
  const handleSend = async (overrideInput?: string) => {
    const textToSend = typeof overrideInput === "string" ? overrideInput : input;
    if (!textToSend.trim() || loading) return;

    const userMessage: Message = { role: "user", content: textToSend };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      abortControllerRef.current = new AbortController();
      const response = await fetch("http://127.0.0.1:8000/api/v1/chat/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: abortControllerRef.current.signal,
        body: JSON.stringify({
          messages: [...messages, userMessage],
          model: selectedModel,
        }),
      });

      // Handle JSON (agent response)
      const contentType = response.headers.get("content-type");
      if (contentType?.includes("application/json")) {
        const data = await response.json();
        if (
          data.type === "agent_response" &&
          data.status === "memory_confirmation_required"
        ) {
          setMemoryConfirmation(data.data);
          setMessages((prev) => [...prev, { role: "assistant", content: data.message }]);
          playTTS(data.message);
          setLoading(false);
          return;
        } else if (
          data.type === "agent_response" &&
          data.status === "confirmation_required"
        ) {
          setOsConfirmation({ request: data.data.request });
          setMessages((prev) => [...prev, { role: "assistant", content: data.message }]);
          playTTS(data.message);
          setLoading(false);
          return;
        } else if (data.type === "agent_response") {
          setMessages((prev) => [...prev, { role: "assistant", content: data.message }]);
          playTTS(data.message);
          setLoading(false);
          return;
        }
      }

      // Handle SSE stream
      if (!response.body) throw new Error("No response body");
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

      let done = false;
      let fullResponseText = "";
      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          const chunkString = decoder.decode(value, { stream: true });
          const lines = chunkString.split("\n\n");
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const dataStr = line.substring(6);
              if (dataStr === "[DONE]") { done = true; break; }
              try {
                const parsed = JSON.parse(dataStr);
                if (parsed.chunk) {
                  fullResponseText += parsed.chunk;
                  setMessages((prev) => {
                    const next = [...prev];
                    const last = next[next.length - 1];
                    next[next.length - 1] = { ...last, content: last.content + parsed.chunk };
                    return next;
                  });
                }
              } catch { /* ignore parse errors */ }
            }
          }
        }
      }
      playTTS(fullResponseText);
    } catch (error: any) {
      if (error.name === "AbortError") {
        console.log("Generation stopped by user");
        return;
      }
      console.error(error);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I encountered an error connecting to the backend.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleSendRef.current = handleSend;
  });

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setLoading(false);
  };

  const handleApproveMemory = async () => {
    if (!memoryConfirmation) return;
    try {
      await fetch("http://127.0.0.1:8000/api/v1/memory/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          collection: memoryConfirmation.collection,
          text: memoryConfirmation.fact,
        }),
      });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Got it! I've saved that to my long-term memory. 🧠" },
      ]);
    } catch {
      console.error("Failed to save memory");
    }
    setMemoryConfirmation(null);
  };

  const handleDenyMemory = () => {
    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: "Okay, I won't save that." },
    ]);
    setMemoryConfirmation(null);
  };

  const handleApproveOs = async () => {
    if (!osConfirmation) return;
    const req = osConfirmation.request;
    setOsConfirmation(null);
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/system/os-agent/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ request: req }),
      });
      const data = await res.json();
      const content = data.message || "Done.";
      setMessages((prev) => [...prev, { role: "assistant", content }]);
      playTTS(content);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I couldn't reach the backend to run that." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleDenyOs = () => {
    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: "Okay, I won't do that." },
    ]);
    setOsConfirmation(null);
  };

  return (
    <div className="flex flex-col h-full bg-black/20 backdrop-blur-md rounded-xl border border-white/5 overflow-hidden">

      {/* ── Toolbar ─────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-4 py-3 bg-black/30 border-b border-white/5 gap-4 flex-wrap">
        {/* Model selector hidden per request */}
        <div className="flex items-center gap-2 min-w-0">
          <Bot size={16} className="text-purple-400 shrink-0" />
          <span className="text-sm font-medium text-white px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg">Omni Core</span>
        </div>

        <div className="flex items-center gap-2">
          {/* Always-on voice loop status (only shown once it reports in) */}
          {voiceLoopState && voiceLoopState !== "stopped" && (
            <span
              className={`flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg border ${
                voiceLoopState === "idle"
                  ? "bg-white/5 border-white/10 text-gray-400"
                  : "bg-green-500/20 border-green-500/40 text-green-300"
              }`}
              title="Always-on voice assistant (configure in Settings)"
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  voiceLoopState === "idle" ? "bg-gray-500" : "bg-green-400 animate-pulse"
                }`}
              />
              {voiceLoopState === "idle" && "Voice: waiting for wake word"}
              {voiceLoopState === "listening" && "Voice: listening…"}
              {voiceLoopState === "thinking" && "Voice: thinking…"}
              {voiceLoopState === "speaking" && "Voice: speaking…"}
            </span>
          )}

          {/* OS Control toggle */}
          <button
            onClick={() => setOsControlAllowed((v) => !v)}
            title={osControlAllowed ? "OS Control ON — Click to disable" : "OS Control OFF — Click to enable"}
            className={`flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg border transition-all ${
              osControlAllowed
                ? "bg-orange-500/20 border-orange-500/40 text-orange-300 hover:bg-orange-500/30"
                : "bg-white/5 border-white/10 text-gray-400 hover:bg-white/10"
            }`}
          >
            {osControlAllowed ? (
              <>
                <ShieldCheck size={14} />
                OS Control: ON
              </>
            ) : (
              <>
                <ShieldOff size={14} />
                OS Control: OFF
              </>
            )}
          </button>
        </div>
      </div>

      {/* ── Messages ──────────────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`flex space-x-3 max-w-[80%] ${
                msg.role === "user"
                  ? "flex-row-reverse space-x-reverse"
                  : "flex-row"
              }`}
            >
              <div
                className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 ${
                  msg.role === "user" ? "bg-blue-500" : "bg-purple-500"
                }`}
              >
                {msg.role === "user" ? (
                  <User size={16} className="text-white" />
                ) : (
                  <Bot size={16} className="text-white" />
                )}
              </div>
              <div
                className={`p-4 rounded-xl ${
                  msg.role === "user"
                    ? "bg-blue-600/20 text-white rounded-tr-none border border-blue-500/20"
                    : "bg-white/5 text-gray-200 rounded-tl-none border border-white/5"
                }`}
              >
                <div className="prose prose-invert max-w-none text-sm">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              </div>
            </div>
          </div>
        ))}

        {/* Loading bubble */}
        {loading && (
          <div className="flex justify-start">
            <div className="flex space-x-3 flex-row">
              <div className="h-8 w-8 rounded-full flex items-center justify-center shrink-0 bg-purple-500">
                <Bot size={16} className="text-white" />
              </div>
              <div className="p-4 rounded-xl bg-white/5 text-gray-200 rounded-tl-none border border-white/5">
                <span className="inline-flex gap-1">
                  <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:0ms]" />
                  <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:150ms]" />
                  <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:300ms]" />
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Memory Confirmation */}
        {memoryConfirmation && (
          <div className="flex justify-start">
            <div className="flex space-x-3 max-w-[80%] flex-row">
              <div className="h-8 w-8 rounded-full flex items-center justify-center shrink-0 bg-yellow-500">
                <Database size={16} className="text-white" />
              </div>
              <div className="p-4 rounded-xl bg-yellow-500/20 text-white rounded-tl-none border border-yellow-500/30">
                <p className="mb-3 text-sm">Would you like me to store this fact?</p>
                <p className="font-mono text-xs bg-black/40 p-2 rounded mb-3">
                  &ldquo;{memoryConfirmation.fact}&rdquo;
                </p>
                <div className="flex space-x-2">
                  <button
                    onClick={handleApproveMemory}
                    className="bg-green-500 hover:bg-green-600 text-white px-3 py-1.5 rounded text-sm transition"
                  >
                    Approve
                  </button>
                  <button
                    onClick={handleDenyMemory}
                    className="bg-red-500 hover:bg-red-600 text-white px-3 py-1.5 rounded text-sm transition"
                  >
                    Deny
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* OS Automation Confirmation */}
        {osConfirmation && (
          <div className="flex justify-start">
            <div className="flex space-x-3 max-w-[80%] flex-row">
              <div className="h-8 w-8 rounded-full flex items-center justify-center shrink-0 bg-orange-500">
                <ShieldCheck size={16} className="text-white" />
              </div>
              <div className="p-4 rounded-xl bg-orange-500/20 text-white rounded-tl-none border border-orange-500/30">
                <p className="mb-3 text-sm">This looks like it could be a sensitive action. Proceed?</p>
                <p className="font-mono text-xs bg-black/40 p-2 rounded mb-3">
                  &ldquo;{osConfirmation.request}&rdquo;
                </p>
                <div className="flex space-x-2">
                  <button
                    onClick={handleApproveOs}
                    className="bg-green-500 hover:bg-green-600 text-white px-3 py-1.5 rounded text-sm transition"
                  >
                    Approve
                  </button>
                  <button
                    onClick={handleDenyOs}
                    className="bg-red-500 hover:bg-red-600 text-white px-3 py-1.5 rounded text-sm transition"
                  >
                    Deny
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── Input Area ────────────────────────────────────────────────────────── */}
      <div className="p-4 bg-black/30 border-t border-white/5">
        <div className="flex gap-2 mb-3 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
          {[
            "Open Notepad and type 'Hello World'",
            "What is my current CPU usage?",
            "Take a screenshot and save it to Downloads"
          ].map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(prompt)}
              disabled={loading || memoryConfirmation !== null || osConfirmation !== null || isListening}
              className="text-xs px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full whitespace-nowrap transition disabled:opacity-50"
            >
              {prompt}
            </button>
          ))}
        </div>
        {isListening && (
          <div className="mb-2 flex items-center gap-2 text-xs text-red-400 animate-pulse">
            <span className="w-2 h-2 rounded-full bg-red-400" />
            Listening… speak now
          </div>
        )}
        <div className="flex items-center space-x-2">
          {/* Voice mic button */}
          {voiceSupported && (
            <button
              onClick={isListening ? stopListening : startListening}
              disabled={loading || memoryConfirmation !== null || osConfirmation !== null}
              title={isListening ? "Stop listening" : "Start voice input"}
              className={`p-3 rounded-lg transition flex-shrink-0 ${
                isListening
                  ? "bg-red-500 hover:bg-red-600 text-white animate-pulse"
                  : "bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white border border-white/10"
              } disabled:opacity-50`}
            >
              {isListening ? <MicOff size={20} /> : <Mic size={20} />}
            </button>
          )}

          <input
            type="text"
            className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm"
            placeholder={isListening ? "Listening…" : "Type your message…"}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            disabled={loading || memoryConfirmation !== null || osConfirmation !== null || isListening}
          />

          {loading ? (
            <button
              onClick={handleStop}
              className="bg-red-500/20 hover:bg-red-500/30 text-red-400 p-3 rounded-lg transition flex-shrink-0"
              title="Stop generation"
            >
              <Square size={20} className="fill-current" />
            </button>
          ) : (
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || memoryConfirmation !== null || osConfirmation !== null}
              className="bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white p-3 rounded-lg transition flex-shrink-0"
            >
              <Send size={20} />
            </button>
          )}
        </div>
      </div>
      {ttsUrl && <audio src={ttsUrl} autoPlay onEnded={() => URL.revokeObjectURL(ttsUrl)} />}
    </div>
  );
}
