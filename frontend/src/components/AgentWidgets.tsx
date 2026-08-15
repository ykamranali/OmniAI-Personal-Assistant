"use client";

import { motion } from "framer-motion";

interface AgentWidgetsProps {
  activeModule?: string;
}

export function AgentWidgets({ activeModule = "idle" }: AgentWidgetsProps) {
  const getWidgetContent = () => {
    switch (activeModule) {
      case "productivity":
        return (
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-cyan-400">Productivity Mode</h3>
            <p className="text-sm text-gray-300">Syncing calendar, tasks, and notes...</p>
            <div className="h-2 w-full bg-gray-700 rounded overflow-hidden">
              <motion.div 
                className="h-full bg-cyan-500" 
                initial={{ width: 0 }} 
                animate={{ width: "100%" }} 
                transition={{ duration: 2, repeat: Infinity }} 
              />
            </div>
          </div>
        );
      case "cybersecurity":
        return (
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-red-400">Cybersecurity Mode</h3>
            <p className="text-sm text-gray-300">Running defensive sweeps & log analysis...</p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-red-500/20 p-2 rounded border border-red-500/30">Firewall: Active</div>
              <div className="bg-green-500/20 p-2 rounded border border-green-500/30">Threats: 0</div>
            </div>
          </div>
        );
      case "coding":
        return (
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-green-400">Coding Assistant</h3>
            <p className="text-sm text-gray-300 font-mono">Analyzing workspace...</p>
            <div className="bg-black/50 p-3 rounded font-mono text-xs border border-green-500/30 text-green-400">
              <p>{`> Executing CI/CD checks`}</p>
              <p className="animate-pulse">{`> _`}</p>
            </div>
          </div>
        );
      default:
        return (
          <div className="flex flex-col items-center justify-center h-full space-y-3 opacity-50">
            <h3 className="text-lg font-medium text-gray-400">Omni Jarvis System</h3>
            <p className="text-xs text-gray-500">Awaiting commands...</p>
          </div>
        );
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full h-48 bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-2xl"
    >
      {getWidgetContent()}
    </motion.div>
  );
}
