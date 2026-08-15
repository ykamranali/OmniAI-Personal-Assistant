import { MemoryManager } from "@/components/MemoryManager";

export default function MemoryPage() {
  return (
    <div className="flex h-screen bg-[#09090b] text-white p-8">
      <div className="flex-1 max-w-6xl mx-auto h-full">
        <MemoryManager />
      </div>
    </div>
  );
}
