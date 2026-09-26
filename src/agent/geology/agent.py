"""Geology research agent definition."""

from google.adk.agents import Agent

from ..config import FAST_CONFIG, MODEL
from .tools import get_geology_report

geology_research_agent = Agent(
    name="geology_research_agent",
    model=MODEL,
    description="地層、地盤、岩石などの地質調査を担当します。",
    instruction=(
        "あなたは地質調査担当です。get_geology_report を必ず1回呼び、"
        "クライアントコンテキストにある緯度・経度をツールに渡してください。\n\n"
        "結果はオーケストレーターが最終回答に組み込むための下書きです。"
        "取得した地質区分・岩相・形成年代をもとに、その大地がどんな環境（海底・火山・河川など）で"
        "どう形成され、今の地形や景観にどうつながっているかを、300字程度の要点にまとめてください。"
        "重要な語句は **太字** にし、見出しや長い前置きは不要です。\n\n"
        "取得に失敗した場合は、その旨と考えられる理由（海域や地質図の"
        "整備範囲外など）を一文で伝えてください。\n\n"
        "最後に「出典: 産総研 シームレス地質図V2」と添えてください。"
    ),
    generate_content_config=FAST_CONFIG,
    tools=[get_geology_report],
    mode="single_turn",
)
