"""Shared model configuration for the agent team."""

import os

from google.adk.models.google_llm import Gemini
from google.genai import types

MODEL_LOCATION = os.getenv("GOOGLE_CLOUD_MODEL_LOCATION", "global")
MODEL = Gemini(
    model=os.getenv("ADK_MODEL", "gemini-3.7-flash"),
    client_kwargs={
        "vertexai": True,
        "location": MODEL_LOCATION,
    },
)
IMAGE_MODEL = os.getenv("ADK_IMAGE_MODEL", "gemini-3.1-flash-image")
# 調査・下書き用の軽い思考設定。応答時間を優先するサブエージェントとツールで使う。
FAST_THINKING = types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW)
FAST_CONFIG = types.GenerateContentConfig(thinking_config=FAST_THINKING)
