"""Root orchestration agent definition."""

from google.adk.agents import Agent

from ..config import MODEL
from ..geology.agent import geology_research_agent
from ..tour.agent import tourism_research_agent
from .tools import create_mock_map_points
from .tools import generate_image


root_agent = Agent(
    name="root_agent",
    model=MODEL,
    description="地質と観光の調査結果を関連付け、画像付きで解説するオーケストレーターです。",
    instruction=(
        "あなたは地質と観光を横断する調査チームのオーケストレーターです。"
        "ユーザーから地域や旅行に関する依頼を受けたら、次の順序を必ず守ってください。"
        "1. geology_research_agent を1回呼び、地質のモック調査結果を得る。"
        "2. tourism_research_agent を1回呼び、観光のモック調査結果を得る。"
        "両エージェントへ、地域名と、入力に含まれる緯度・経度・送信時刻を省略せず渡す。"
        "3. 二つの結果を比較し、地形や地質が景観、散策、文化体験にどう関係するかを"
        "一つの解説として日本語で分かりやすくまとめる。単なる二つの回答の列挙にしない。"
        "4. create_mock_map_points を1回呼び、地域名と緯度・経度を渡して地図用座標を返す。"
        "5. 統合した解説を視覚的に補助する、文字なしの旅行イラスト用プロンプトを作り、"
        "generate_image を1回呼ぶ。地質的な景観と観光体験の両方を1枚に含める。"
        "6. 最終回答は『地質と観光のつながり』『おすすめの過ごし方』『注意点』を含め、"
        "調査情報と地図地点がモックであること、画像が生成イメージであることを明記する。"
        "ユーザーが画像だけを求めた場合も、対象地域を推定できるなら同じ流れを実行する。"
    ),
    sub_agents=[
        geology_research_agent,
        tourism_research_agent,
    ],
    tools=[create_mock_map_points, generate_image],
)
