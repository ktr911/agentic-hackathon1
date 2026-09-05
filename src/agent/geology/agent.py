"""Geology research agent definition."""

from google.adk.agents import Agent

from ..config import MODEL
from .tools import get_geology_report

geology_research_agent = Agent(
    name="geology_research_agent",
    model=MODEL,
    description="地層、地盤、岩石などの地質調査を担当します。",
    instruction=(
        "あなたは地質調査担当です。get_geology_report を必ず1回呼び、"
        "クライアントコンテキストにある緯度・経度をツールに渡してください。"
        "取得した地質区分・岩相・形成年代をもとに、その土地がどんな岩石で"
        "どのように形成されたのかを日本語で分かりやすく解説してください。"
        "取得に失敗した場合は、その旨と考えられる理由（海域や地質図の"
        "整備範囲外など）を伝えてください。"
        "情報の出典（産総研シームレス地質図V2）を明記してください。"
    ),
    tools=[get_geology_report],
    mode="single_turn",
)
