from fastapi import APIRouter
from app.services.llm import llm_service

router = APIRouter(prefix="/models", tags=["models"])

@router.get("/")
async def list_models():
    models = await llm_service.get_models()
    return {"status": "success", "data": models}
