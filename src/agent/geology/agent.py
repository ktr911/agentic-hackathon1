"""Geology research agent definition."""

from google.adk.agents import Agent

from ..config import MODEL
from .tools import get_mock_geology_report


geology_research_agent = Agent(
    name="geology_research_agent",
    model=MODEL,
    description="地層、地盤、岩石などの地質調査を担当します。",
    instruction=(
        "あなたは地質調査担当です。get_mock_geology_report を必ず1回呼び、"
        "クライアントコンテキストに緯度・経度があればツールにも渡してください。"
        "その結果だけを日本語で簡潔に整理してください。"
        "結果がモックデータであり、実地調査ではないことを明記してください。"
    ),
    tools=[get_mock_geology_report],
    mode="single_turn",
)
