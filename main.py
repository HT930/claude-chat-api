"""
Claude Chat API - ポートフォリオ用デモ
FastAPI + Anthropic Claude API によるチャットバックエンド
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import anthropic
import os
import json
from datetime import datetime

app = FastAPI(
    title="Claude Chat API",
    description="Anthropic Claude APIを使ったチャットバックエンド",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Schemas ---

class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: list[Message]
    system_prompt: Optional[str] = "あなたは親切なAIアシスタントです。日本語で回答してください。"
    model: Optional[str] = "claude-sonnet-4-6"
    max_tokens: Optional[int] = 1024
    stream: Optional[bool] = False

class ChatResponse(BaseModel):
    reply: str
    model: str
    usage: dict
    timestamp: str

# --- Routes ---

@app.get("/")
def root():
    return {
        "service": "Claude Chat API",
        "version": "1.0.0",
        "endpoints": ["/chat", "/chat/stream", "/health", "/docs"],
    }

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    通常チャットエンドポイント（レスポンス一括返却）
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY が設定されていません")

    client = anthropic.Anthropic(api_key=api_key)

    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    try:
        response = client.messages.create(
            model=req.model,
            max_tokens=req.max_tokens,
            system=req.system_prompt,
            messages=messages,
        )
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Claude API エラー: {str(e)}")

    return ChatResponse(
        reply=response.content[0].text,
        model=response.model,
        usage={
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
        timestamp=datetime.utcnow().isoformat(),
    )


@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    """
    ストリーミングチャットエンドポイント（Server-Sent Events）
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY が設定されていません")

    client = anthropic.Anthropic(api_key=api_key)
    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    def event_generator():
        try:
            with client.messages.stream(
                model=req.model,
                max_tokens=req.max_tokens,
                system=req.system_prompt,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {json.dumps({'text': text})}\n\n"
            yield "data: [DONE]\n\n"
        except anthropic.APIError as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
