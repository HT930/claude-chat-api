# Claude Chat API 🤖

Anthropic Claude API を使った **FastAPI チャットバックエンド**のポートフォリオサンプルです。  
通常チャットとストリーミングチャットの両方に対応しています。

## 機能

| 機能 | 詳細 |
|------|------|
| ✅ 通常チャット | `POST /chat` でメッセージを送信、全文を一括で受け取る |
| ✅ ストリーミング | `POST /chat/stream` でServer-Sent Events によるリアルタイム返答 |
| ✅ システムプロンプト | リクエストごとにカスタマイズ可能 |
| ✅ モデル選択 | `claude-sonnet-4-6` など任意のモデルを指定 |
| ✅ Swagger UI | `/docs` で自動生成されたAPI仕様書 |
| ✅ CORS対応 | フロントエンドと分離したデプロイに対応 |

## セットアップ

```bash
# 1. リポジトリをクローン
git clone https://github.com/yourname/claude-chat-api.git
cd claude-chat-api

# 2. 依存関係のインストール
pip install -r requirements.txt

# 3. 環境変数の設定
cp .env.example .env
# .env を編集して ANTHROPIC_API_KEY を設定

# 4. サーバー起動
uvicorn main:app --reload
```

## API 使用例

### 通常チャット

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "こんにちは！"}],
    "system_prompt": "あなたは丁寧なアシスタントです。"
  }'
```

**レスポンス例:**
```json
{
  "reply": "こんにちは！何かお手伝いできることはありますか？",
  "model": "claude-sonnet-4-6",
  "usage": { "input_tokens": 25, "output_tokens": 18 },
  "timestamp": "2026-05-11T10:00:00"
}
```

### ストリーミングチャット

```bash
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "日本の首都は？"}]}'
```

## 技術スタック

- **FastAPI** — 高速・型安全なPython Webフレームワーク
- **Anthropic Python SDK** — Claude API クライアント
- **Pydantic v2** — データバリデーション
- **Uvicorn** — ASGI サーバー

## デプロイ

Railway / Render / Fly.io などにそのままデプロイ可能です。  
環境変数 `ANTHROPIC_API_KEY` をホスティング側で設定してください。

## ライセンス

MIT
