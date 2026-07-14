import json
import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from anyio import to_thread  # 用于将同步阻塞流平滑桥接到 FastAPI 的异步循环中

router = APIRouter(prefix="/v1", tags=["AI Router"])

OLLAMA_URL = "http://127.0.0.1:11434/v1/chat/completions"

class ChatRequest(BaseModel):
    model: str = "deepseek-r1:8b"
    messages: list[dict[str, str]]
    stream: bool = True

def sync_ollama_stream(chat_history: list, model: str):
    """
    同步阻塞流生成器：使用最稳健的 requests.post(stream=True)，不设置 timeout。
    无论 Ollama 加载模型花 30 秒还是 1 分钟，它都会雷打不动地死等，绝不提前掐断！
    """
    payload = {
        "model": model,
        "messages": chat_history,
        "stream": True
    }
    
    try:
        # stream=True 且不传 timeout 参数，这意味着无限期等待首字
        with requests.post(OLLAMA_URL, json=payload, stream=True) as response:
            if response.status_code != 200:
                yield f"data: [Error] Ollama returned status code {response.status_code}\n\n"
                return
            
            # 逐行读取标准输入流
            for line in response.iter_lines():
                if line:
                    # line 是 bytes，解码后原封不动透明转发给前端
                    decoded_line = line.decode('utf-8').strip()
                    yield f"{decoded_line}\n\n"
                    
    except Exception as exc:
        yield f"data: [Error] Synchronous bridge failed: {exc}\n\n"

async def async_generator_bridge(chat_history: list, model: str):
    """
    桥接器：通过 anyio.to_thread 将同步的死等流，安全、不卡死线程地喂给 FastAPI 的异步容器
    """
    # 将同步迭代器安全包裹，防止其阻塞 FastAPI 的 ASGI 主事件循环
    for token in sync_ollama_stream(chat_history, model):
        yield token

@router.post("/chat/completions")
async def chat_endpoint(request: ChatRequest):
    try:
        print(f"[Router] Incoming chat history length: {len(request.messages)} rounds.")
        
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
        raise HTTPException(status_code=500, detail=f"Gateway Internal Error: {str(e)}")
    
    