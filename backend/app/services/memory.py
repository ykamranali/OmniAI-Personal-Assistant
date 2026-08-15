import chromadb
import uuid
import os
from typing import List, Dict, Any, Optional
from app.core.config import settings

class MemoryService:
    def __init__(self):
        # Create chroma directory if it doesn't exist
        os.makedirs(settings.CHROMA_PATH, exist_ok=True)
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
        
        # We will use distinct collections for different types of memories
        self.collections = {
            "notes": self.client.get_or_create_collection("notes"),
            "projects": self.client.get_or_create_collection("projects"),
            "preferences": self.client.get_or_create_collection("preferences"),
            "general": self.client.get_or_create_collection("general")
        }

    def store_memory(self, collection_name: str, text: str, metadata: Dict[str, Any] = None) -> str:
        """Store a new memory snippet into the specified collection."""
        if collection_name not in self.collections:
            collection_name = "general"
            
        memory_id = str(uuid.uuid4())
        meta = metadata or {}
        meta["timestamp"] = __import__('datetime').datetime.now().isoformat()
        
        self.collections[collection_name].add(
            documents=[text],
            metadatas=[meta],
            ids=[memory_id]
        )
        return memory_id

    def search_memory(self, collection_name: str, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search memory by semantic similarity."""
        if collection_name not in self.collections:
            collection_name = "general"
            
        results = self.collections[collection_name].query(
            query_texts=[query],
            n_results=n_results
        )
        
        formatted_results = []
        if results and results.get("documents") and len(results["documents"]) > 0:
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {}
                })
        return formatted_results

    def delete_memory(self, collection_name: str, memory_id: str) -> bool:
        """Delete a specific memory by ID."""
        if collection_name not in self.collections:
            return False
            
        try:
            self.collections[collection_name].delete(ids=[memory_id])
            return True
        except Exception as e:
            print(f"Error deleting memory: {e}")
            return False

    def get_all_memories(self, collection_name: str) -> List[Dict[str, Any]]:
        """Retrieve all memories in a collection for the Memory Manager UI."""
        if collection_name not in self.collections:
            return []
            
        results = self.collections[collection_name].get()
        
        formatted_results = []
        if results and results.get("documents"):
            for i in range(len(results["documents"])):
                formatted_results.append({
                    "id": results["ids"][i],
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i] if results.get("metadatas") else {}
                })
        return formatted_results

memory_service = MemoryService()
