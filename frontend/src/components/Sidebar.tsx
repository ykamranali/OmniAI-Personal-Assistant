"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  MessageSquare,
  Database,
  Settings,
  Wifi,
  WifiOff,
  Zap,
} from "lucide-react";

export function Sidebar() {
  const pathname = usePathname();
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [activeModel, setActiveModel] = useState<string>("");

  // ── Poll backend health ───────────────────────────────────────────────────
  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/health", {
          signal: AbortSignal.timeout(3000),
        });
        setBackendOnline(res.ok);

        // Also grab the active model from runtime settings
        if (res.ok) {
          const settingsRes = await fetch(
            "http://127.0.0.1:8000/api/v1/system/settings",
            { signal: AbortSignal.timeout(3000) }
          );
          if (settingsRes.ok) {
            const data = await settingsRes.json();
            if (data.status === "success" && data.data.default_model) {
              setActiveModel(data.data.default_model);
            }
          }
        }
      } catch {
        setBackendOnline(false);
      }
    };

    check();
    const interval = setInterval(check, 15000); // re-check every 15s
    return () => clearInterval(interval);
  }, []);

  const links = [
    { href: "/", label: "Dashboard", icon: LayoutDashboard },
    { href: "/chat", label: "Agent Chat", icon: MessageSquare },
    { href: "/memory", label: "Memory Core", icon: Database },
    { href: "/settings", label: "Settings", icon: Settings },
  ];

  return (
    <div className="w-64 h-screen border-r border-white/5 bg-black/40 backdrop-blur-md flex flex-col fixed left-0 top-0 z-50">
      {/* ── Logo ─────────────────────────────────────────────────────────────── */}
      <div className="p-6 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center shadow-lg shadow-purple-500/30">
            <Zap size={16} className="text-white" />
          </div>
          <h2 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-blue-400">
            Omni AI
          </h2>
        </div>

        {/* Backend status pill */}
        <div
          className={`mt-3 flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border w-fit ${
            backendOnline === null
              ? "border-gray-700 text-gray-500"
              : backendOnline
              ? "border-green-500/30 text-green-400 bg-green-500/10"
              : "border-red-500/30 text-red-400 bg-red-500/10"
          }`}
        >
          {backendOnline === null ? (
            <>
              <div className="w-1.5 h-1.5 rounded-full bg-gray-500" />
              Connecting…
            </>
          ) : backendOnline ? (
            <>
              <Wifi size={11} />
              Backend Online
            </>
          ) : (
            <>
              <WifiOff size={11} />
              Backend Offline
            </>
          )}
        </div>
      </div>

      {/* ── Nav ──────────────────────────────────────────────────────────────── */}
      <nav className="flex-1 px-4 space-y-1 mt-2">
        {links.map((link) => {
          const Icon = link.icon;
          const isActive = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-all ${
                isActive
                  ? "bg-white/10 text-white shadow-sm"
                  : "text-gray-400 hover:bg-white/5 hover:text-white"
              }`}
            >
              <Icon
                size={20}
                className={isActive ? "text-purple-400" : ""}
              />
              <span className="font-medium text-sm">{link.label}</span>
              {isActive && (
                <span className="ml-auto w-1.5 h-1.5 rounded-full bg-purple-400" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* ── Footer ───────────────────────────────────────────────────────────── */}
      <div className="p-4 border-t border-white/5 space-y-3">


        {/* User info */}
        <div className="flex items-center space-x-3">
          <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-green-400 to-blue-500 flex items-center justify-center border border-white/20 shrink-0">
            <span className="text-xs font-bold text-white">US</span>
          </div>
          <div className="text-sm min-w-0">
            <p className="font-medium text-white">User</p>
            <p
              className={`text-xs ${
                backendOnline ? "text-green-400" : "text-gray-500"
              }`}
            >
              {backendOnline ? "System Online" : "System Offline"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
