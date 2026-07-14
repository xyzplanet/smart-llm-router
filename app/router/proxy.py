import json
import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/v1", tags=["AI Router"])

OLLAMA_URL = "http://127.0.0.1:11434/v1/chat/completions"

class ChatRequest(BaseModel):
    model: str = "deepseek-r1:8b"
    messages: list[dict[str, str]]
    stream: bool = True

def sync_ollama_stream(chat_history: list, model: str):
    payload = {
        "model": model,
        "messages": chat_history,
        "stream": True
    }
    try:
        # 使用原生 requests 死等，移除所有超时时间
        with requests.post(OLLAMA_URL, json=payload, stream=True) as response:
            if response.status_code != 200:
                yield f"data: [Error] Ollama returned status code {response.status_code}\n\n"
                return
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8').strip()
                    yield f"{decoded_line}\n\n"
    except Exception as exc:
        yield f"data: [Error] Proxy stream bridge failed: {exc}\n\n"

async def async_generator_bridge(chat_history: list, model: str):
    for token in sync_ollama_stream(chat_history, model):
        yield token

@router.post("/chat/completions")
async def chat_endpoint(request: ChatRequest):
    try:
        print(f"[Router Proxy] Incoming chat history length: {len(request.messages)} rounds.")
        headers = {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
        return StreamingResponse(
            async_generator_bridge(request.messages, request.model),
            headers=headers
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy Gateway Error: {str(e)}")



