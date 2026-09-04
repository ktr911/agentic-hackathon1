import os

from fastapi import FastAPI
from google import genai

app = FastAPI()

# Vertex AI 経由で Gemini API を利用する
# ローカル実行時は `gcloud auth application-default login` が必要
# Cloud Run 実行時はサービスアカウントの権限で自動的に認証される
_client = genai.Client(
    vertexai=True,
    project=os.environ.get("GOOGLE_CLOUD_PROJECT", "agentic-ai-hackathon-test1"),
    location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
)
_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


@app.get("/")
def read_root():
    return {"message": "Hello from Cloud Run!"}


@app.get("/chat")
def chat(q: str = "自己紹介してください"):
    response = _client.models.generate_content(model=_MODEL, contents=q)
    return {"prompt": q, "response": response.text}
