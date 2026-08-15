"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";

export function JarvisVisualizer({ isActive = false }: { isActive?: boolean }) {
  const [pulse, setPulse] = useState(1);

  useEffect(() => {
    if (isActive) {
      const interval = setInterval(() => {
        setPulse((prev) => (prev === 1 ? 1.2 : 1));
      }, 800);
      return () => clearInterval(interval);
    }
  }, [isActive]);

  return (
    <div className="relative flex items-center justify-center w-64 h-64 mx-auto my-12">
      {/* Outer Glow */}
      <motion.div
        animate={{
          scale: isActive ? [1, 1.3, 1] : 1,
          opacity: isActive ? [0.3, 0.6, 0.3] : 0.2,
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        className="absolute w-full h-full rounded-full bg-cyan-500 blur-3xl opacity-30"
      />

      {/* Inner Core */}
      <motion.div
        animate={{
          scale: pulse,
          boxShadow: isActive 
            ? "0 0 40px 10px rgba(6, 182, 212, 0.7)" 
            : "0 0 15px 2px rgba(6, 182, 212, 0.3)",
        }}
        transition={{
          duration: 0.8,
          ease: "easeInOut",
        }}
        className="relative z-10 w-32 h-32 rounded-full bg-gradient-to-br from-cyan-300 via-blue-500 to-purple-600 flex items-center justify-center overflow-hidden border border-white/20 backdrop-blur-md"
      >
        <div className="absolute inset-0 bg-black/10 mix-blend-overlay"></div>
        <div className="w-16 h-16 rounded-full bg-white/20 blur-xl"></div>
      </motion.div>
      
      {/* Ring */}
      <motion.div
        animate={{ rotate: 360 }}
        transition={{
          duration: 10,
          repeat: Infinity,
          ease: "linear",
        }}
        className="absolute w-48 h-48 rounded-full border border-dashed border-cyan-400/50"
      />
      <motion.div
        animate={{ rotate: -360 }}
        transition={{
          duration: 15,
          repeat: Infinity,
          ease: "linear",
        }}
        className="absolute w-56 h-56 rounded-full border border-dotted border-blue-400/30"
      />
    </div>
  );
}
