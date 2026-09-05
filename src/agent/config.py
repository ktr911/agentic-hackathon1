"""Shared model configuration for the agent team."""

import os


MODEL = os.getenv("ADK_MODEL", "gemini-3.7-flash")
IMAGE_MODEL = os.getenv("ADK_IMAGE_MODEL", "gemini-3.1-flash-image")
