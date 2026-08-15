"use client";

import { useState, useEffect } from "react";
import { Database, Trash2, Search, RefreshCw, Plus, X, Tag } from "lucide-react";

type Memory = {
  id: string;
  text: string;
  metadata: Record<string, string>;
};

const COLLECTIONS = [
  { id: "general", label: "General", color: "blue" },
  { id: "notes", label: "Notes", color: "purple" },
  { id: "projects", label: "Projects", color: "green" },
  { id: "preferences", label: "Preferences", color: "pink" },
] as const;

type CollectionId = (typeof COLLECTIONS)[number]["id"];

const TAB_COLORS: Record<string, string> = {
  blue: "text-blue-400 border-blue-400 bg-blue-400/10",
  purple: "text-purple-400 border-purple-400 bg-purple-400/10",
  green: "text-green-400 border-green-400 bg-green-400/10",
  pink: "text-pink-400 border-pink-400 bg-pink-400/10",
};

const DOT_COLORS: Record<string, string> = {
  blue: "bg-blue-400",
  purple: "bg-purple-400",
  green: "bg-green-400",
  pink: "bg-pink-400",
};

export function MemoryManager() {
  const [activeCollection, setActiveCollection] = useState<CollectionId>("general");
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  // Add memory form
  const [showAddForm, setShowAddForm] = useState(false);
  const [newMemoryText, setNewMemoryText] = useState("");
  const [addingMemory, setAddingMemory] = useState(false);
  const [addError, setAddError] = useState("");

  // ── Fetch ─────────────────────────────────────────────────────────────────
  const fetchMemories = async (collection: CollectionId = activeCollection) => {
    setLoading(true);
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/api/v1/memory/?collection=${collection}`
      );
      const data = await res.json();
      if (data.status === "success") setMemories(data.data);
    } catch {
      console.error("Failed to fetch memories");
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchMemories(activeCollection);
    setTimeout(() => setSearchQuery(""), 0);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeCollection]);

  // ── Search ────────────────────────────────────────────────────────────────
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      fetchMemories();
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/api/v1/memory/search?query=${encodeURIComponent(
          searchQuery
        )}&collection=${activeCollection}`
      );
      const data = await res.json();
      if (data.status === "success") setMemories(data.data);
    } catch {
      console.error("Search failed");
    }
    setLoading(false);
  };

  // ── Delete ────────────────────────────────────────────────────────────────
  const handleDelete = async (id: string) => {
    try {
      await fetch(
        `http://127.0.0.1:8000/api/v1/memory/${activeCollection}/${id}`,
        { method: "DELETE" }
      );
      setMemories((prev) => prev.filter((m) => m.id !== id));
    } catch {
      console.error("Delete failed");
    }
  };

  // ── Add Memory ────────────────────────────────────────────────────────────
  const handleAddMemory = async () => {
    if (!newMemoryText.trim()) return;
    setAddingMemory(true);
    setAddError("");
    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/memory/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          collection: activeCollection,
          text: newMemoryText.trim(),
        }),
      });
      if (!res.ok) throw new Error("Server error");
      setNewMemoryText("");
      setShowAddForm(false);
      await fetchMemories();
    } catch {
      setAddError("Failed to save. Is the backend running?");
    }
    setAddingMemory(false);
  };

  const activeCollectionMeta = COLLECTIONS.find((c) => c.id === activeCollection)!;

  return (
    <div className="glass rounded-xl p-6 h-full flex flex-col text-white">
      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center space-x-2">
          <Database className="text-blue-400" />
          <h2 className="text-2xl font-semibold">Memory Manager</h2>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAddForm((v) => !v)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/30 text-purple-300 rounded-lg transition"
          >
            {showAddForm ? <X size={14} /> : <Plus size={14} />}
            {showAddForm ? "Cancel" : "Add Memory"}
          </button>
          <button
            onClick={() => fetchMemories()}
            className="p-2 hover:bg-white/10 rounded-full transition"
            title="Refresh"
          >
            <RefreshCw size={18} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {/* ── Collection Tabs ─────────────────────────────────────────────────── */}
      <div className="flex gap-2 mb-5 flex-wrap">
        {COLLECTIONS.map((col) => {
          const isActive = col.id === activeCollection;
          return (
            <button
              key={col.id}
              onClick={() => setActiveCollection(col.id)}
              className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-medium border transition-all ${
                isActive
                  ? TAB_COLORS[col.color]
                  : "border-white/10 text-gray-400 hover:text-white hover:border-white/20"
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${isActive ? DOT_COLORS[col.color] : "bg-gray-600"}`}
              />
              {col.label}
            </button>
          );
        })}
      </div>

      {/* ── Add Memory Form ─────────────────────────────────────────────────── */}
      {showAddForm && (
        <div className="mb-5 p-4 bg-white/3 border border-white/10 rounded-xl">
          <div className="flex items-center gap-2 mb-3 text-sm text-gray-300">
            <Tag size={14} />
            <span>
              Adding to <strong className="text-white">{activeCollectionMeta.label}</strong> collection
            </span>
          </div>
          <textarea
            value={newMemoryText}
            onChange={(e) => setNewMemoryText(e.target.value)}
            placeholder="Enter the memory or fact to store…"
            rows={3}
            className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-sm text-white resize-none focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          {addError && (
            <p className="mt-2 text-xs text-red-400">{addError}</p>
          )}
          <div className="flex justify-end mt-3">
            <button
              onClick={handleAddMemory}
              disabled={addingMemory || !newMemoryText.trim()}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white text-sm rounded-lg transition"
            >
              {addingMemory ? (
                <RefreshCw size={14} className="animate-spin" />
              ) : (
                <Plus size={14} />
              )}
              {addingMemory ? "Saving…" : "Save Memory"}
            </button>
          </div>
        </div>
      )}

      {/* ── Search ─────────────────────────────────────────────────────────── */}
      <div className="flex space-x-2 mb-5">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder={`Search ${activeCollectionMeta.label} memories…`}
          className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={handleSearch}
          className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition flex items-center space-x-2"
        >
          <Search size={16} />
          <span className="text-sm">Search</span>
        </button>
        {searchQuery && (
          <button
            onClick={() => { setSearchQuery(""); fetchMemories(); }}
            className="px-3 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm text-gray-400 hover:text-white transition"
          >
            Clear
          </button>
        )}
      </div>

      {/* ── Memory count ───────────────────────────────────────────────────── */}
      {!loading && (
        <p className="text-xs text-gray-500 mb-3">
          {memories.length} {memories.length === 1 ? "entry" : "entries"} in{" "}
          <span className="text-gray-400">{activeCollectionMeta.label}</span>
        </p>
      )}

      {/* ── List ───────────────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-1">
        {loading ? (
          <div className="flex items-center justify-center gap-2 text-gray-400 py-12">
            <RefreshCw size={18} className="animate-spin" />
            Loading memories…
          </div>
        ) : memories.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Database size={32} className="text-gray-700 mb-3" />
            <p className="text-gray-400 text-sm">No memories found.</p>
            <p className="text-gray-600 text-xs mt-1">
              {searchQuery
                ? "Try a different search term."
                : `Use the "Add Memory" button or chat with OmniAI to populate this collection.`}
            </p>
          </div>
        ) : (
          memories.map((mem) => (
            <div
              key={mem.id}
              className="bg-white/5 border border-white/10 p-4 rounded-lg flex justify-between items-start group hover:border-white/20 transition"
            >
              <div className="flex-1 min-w-0">
                <p className="text-gray-200 text-sm leading-relaxed">{mem.text}</p>
                <div className="flex items-center gap-3 text-xs text-gray-600 mt-2">
                  <span className="font-mono">
                    {mem.id.substring(0, 8)}…
                  </span>
                  {mem.metadata?.timestamp && (
                    <span>
                      {new Date(mem.metadata.timestamp).toLocaleString()}
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={() => handleDelete(mem.id)}
                className="ml-3 text-red-400 opacity-0 group-hover:opacity-100 p-2 hover:bg-red-500/20 rounded transition shrink-0"
                title="Delete memory"
              >
                <Trash2 size={15} />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
