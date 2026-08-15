"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Zap, Wifi, WifiOff, Settings } from "lucide-react";

export function TopBar() {
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  // ── Poll backend health ───────────────────────────────────────────────────
  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/health", {
          signal: AbortSignal.timeout(3000),
        });
        setBackendOnline(res.ok);
      } catch {
        setBackendOnline(false);
      }
    };
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="flex items-center justify-between px-5 py-3 border-b border-white/5 bg-black/40 backdrop-blur-md shrink-0">
      <div className="flex items-center gap-2.5">
        <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center shadow-lg shadow-purple-500/30">
          <Zap size={16} className="text-white" />
        </div>
        <h1 className="text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-blue-400">
          Omni AI
        </h1>
        <span
          className={`inline-flex items-center gap-1.5 ml-1 px-2.5 py-1 rounded-full text-xs font-medium border ${
            backendOnline === null
              ? "border-gray-700 text-gray-500"
              : backendOnline
              ? "border-green-500/30 text-green-400 bg-green-500/10"
              : "border-red-500/30 text-red-400 bg-red-500/10"
          }`}
        >
          {backendOnline === null ? (
            "Connecting…"
          ) : backendOnline ? (
            <>
              <Wifi size={11} /> Online
            </>
          ) : (
            <>
              <WifiOff size={11} /> Offline
            </>
          )}
        </span>
      </div>

      <Link
        href="/settings"
        title="Settings"
        className="p-2.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition"
      >
        <Settings size={20} />
      </Link>
    </header>
  );
}
