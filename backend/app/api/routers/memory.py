from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.services.memory import memory_service

router = APIRouter(prefix="/memory", tags=["memory"])

class StoreMemoryRequest(BaseModel):
    collection: str
    text: str
    metadata: Optional[Dict[str, Any]] = None

@router.post("/")
async def store_memory(request: StoreMemoryRequest):
    mem_id = memory_service.store_memory(request.collection, request.text, request.metadata)
    return {"status": "success", "id": mem_id}

@router.get("/")
async def get_all_memories(collection: str = "general"):
    results = memory_service.get_all_memories(collection)
    return {"status": "success", "data": results}

@router.get("/search")
async def search_memory(query: str, collection: str = "general", n_results: int = 5):
    results = memory_service.search_memory(collection, query, n_results)
    return {"status": "success", "data": results}

@router.delete("/{collection}/{memory_id}")
async def delete_memory(collection: str, memory_id: str):
    success = memory_service.delete_memory(collection, memory_id)
    if success:
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Memory not found or deletion failed")
