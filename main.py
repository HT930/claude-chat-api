"""
Gemini Chat API - ポートフォリオ用デモ
FastAPI + Google Gemini API によるチャットバックエンド
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import google.generativeai as genai
import os
import json
from datetime import datetime

app = FastAPI(
    title="Gemini Chat API",
    description="Google Gemini APIを使ったチャットバックエンド",
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
    model: Optional[str] = "gemini-2.0-flash"
    max_tokens: Optional[int] = 1024
    stream: Optional[bool] = False

class ChatResponse(BaseModel):
    reply: str
    model: str
    usage: dict
    timestamp: str

# --- Helpers ---

def build_gemini_history(messages: list[Message]) -> tuple[list[dict], str]:
    """Convert messages to Gemini format. Returns (history, last_user_message)."""
    history = []
    for m in messages[:-1]:
        role = "model" if m.role == "assistant" else "user"
        history.append({"role": role, "parts": [m.content]})
    last = messages[-1].content
    return history, last

# --- Routes ---

@app.get("/")
def root():
    return {
        "service": "Gemini Chat API",
        "version": "1.0.0",
        "endpoints": ["/chat", "/chat/stream", "/health", "/docs"],
    }

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY が設定されていません")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=req.model,
        system_instruction=req.system_prompt,
    )

    history, last_message = build_gemini_history(req.messages)

    try:
        chat_session = model.start_chat(history=history)
        response = chat_session.send_message(last_message)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gemini API エラー: {str(e)}")

    usage = {}
    if response.usage_metadata:
        usage = {
            "input_tokens": response.usage_metadata.prompt_token_count,
            "output_tokens": response.usage_metadata.candidates_token_count,
        }

    return ChatResponse(
        reply=response.text,
        model=req.model,
        usage=usage,
        timestamp=datetime.utcnow().isoformat(),
    )


@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY が設定されていません")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=req.model,
        system_instruction=req.system_prompt,
    )

    history, last_message = build_gemini_history(req.messages)

    def event_generator():
        try:
            chat_session = model.start_chat(history=history)
            for chunk in chat_session.send_message(last_message, stream=True):
                if chunk.text:
                    yield f"data: {json.dumps({'text': chunk.text})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
