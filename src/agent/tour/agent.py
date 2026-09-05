"""Tourism research agent definition."""

from google.adk.agents import Agent

from ..config import MODEL
from .tools import get_mock_tourism_report


tourism_research_agent = Agent(
    name="tourism_research_agent",
    model=MODEL,
    description="観光地、旅行プラン、地域の見どころの調査を担当します。",
    instruction=(
        "あなたは観光調査担当です。get_mock_tourism_report を必ず1回呼び、"
        "クライアントコンテキストに緯度・経度があればツールにも渡してください。"
        "その結果だけを日本語で簡潔に整理してください。"
        "結果がモックデータであり、実際の観光情報ではないことを明記してください。"
    ),
    tools=[get_mock_tourism_report],
    mode="single_turn",
)
