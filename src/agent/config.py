"""Shared model configuration for the agent team."""

import os

from google.adk.models.google_llm import Gemini

MODEL_LOCATION = os.getenv("GOOGLE_CLOUD_MODEL_LOCATION", "global")
MODEL = Gemini(
    model=os.getenv("ADK_MODEL", "gemini-3.7-flash"),
    client_kwargs={
        "vertexai": True,
        "location": MODEL_LOCATION,
    },
)
IMAGE_MODEL = os.getenv("ADK_IMAGE_MODEL", "gemini-3.1-flash-image")
