"""Geology research agent definition."""

from google.adk.agents import Agent

from ..config import MODEL
from .tools import get_geology_report
from .tools import get_mock_geology_report


geology_research_agent = Agent(
    name="geology_research_agent",
    model=MODEL,
    description="地層、地盤、岩石、断層、地形形成史などの地球科学・地質調査を担当する専門エージェントです。",
    instruction=(
        "あなたは地質学・地球科学の調査専門員です。"
        "`get_geology_report` を呼び出して対象地域および緯度・経度の大地の成り立ち、地層、岩相、断層、地形特徴を調査してください。"
        "得られた調査結果を基に、大地の成り立ちや代表的な岩石・観察ポイントを日本語で分かりやすく整理して回答してください。"
    ),
    tools=[get_geology_report, get_mock_geology_report],
    mode="single_turn",
)
