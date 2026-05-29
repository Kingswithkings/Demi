from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def chat_with_demi(request: ChatRequest):
    return {"reply": f"Demi received: {request.message}"}
