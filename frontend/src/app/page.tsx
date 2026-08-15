import { ChatInterface } from "@/components/ChatInterface";
import { JarvisVisualizer } from "@/components/JarvisVisualizer";
import { AgentWidgets } from "@/components/AgentWidgets";

export default function Home() {
  return (
    <div className="flex flex-col h-full bg-[#050505] text-white p-4 overflow-hidden relative">
      {/* Background aesthetics */}
      <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-10 pointer-events-none mix-blend-overlay"></div>
      <div className="absolute top-0 inset-x-0 h-40 bg-gradient-to-b from-cyan-900/20 to-transparent pointer-events-none"></div>
      <div className="absolute bottom-0 inset-x-0 h-64 bg-gradient-to-t from-purple-900/10 to-transparent pointer-events-none"></div>

      <div className="flex-1 max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-6 relative z-10">
        
        {/* Left Column: Visualizer & Widgets */}
        <div className="lg:col-span-5 flex flex-col items-center justify-center space-y-8 h-full py-8">
          <div className="text-center space-y-2">
            <h1 className="text-4xl font-light tracking-widest text-white/90">OMNI <span className="font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-600">JARVIS</span></h1>
            <p className="text-xs text-gray-500 uppercase tracking-[0.3em]">System Online</p>
          </div>
          
          {/* Visualizer - we can pass isActive dynamically if we connect state later, hardcoding true for visual effect now */}
          <JarvisVisualizer isActive={true} />

          {/* Widgets */}
          <div className="w-full max-w-sm">
            <AgentWidgets activeModule="idle" />
          </div>
        </div>

        {/* Right Column: Chat Interface */}
        <div className="lg:col-span-7 h-full flex flex-col shadow-2xl rounded-2xl overflow-hidden border border-white/5 bg-black/40 backdrop-blur-3xl">
          <ChatInterface />
        </div>
        
      </div>
    </div>
  );
}
