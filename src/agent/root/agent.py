"""Root orchestration agent definition with interactive geo-tour routing."""

from google.adk.agents import Agent

from ..config import MODEL
from ..geology.agent import geology_research_agent
from ..tour.agent import tourism_research_agent
from .tools import create_map_points, create_mock_map_points, generate_image

root_agent = Agent(
    name="root_agent",
    model=MODEL,
    description="地質と観光を融合し、地質連動ルートの提案・サジェストとユーザー対話を統括するオーケストレーターです。",
    instruction=(
        "あなたは地質と観光を横断する調査チームのオーケストレーターです。"
        "ユーザーのメッセージ（初回リクエスト、またはルート選択や深掘りの返答）に応じて、柔軟に進行してください。\n\n"
        "【ケース1：初回提案・新しい地域の調査の場合】\n"
        "1. 最初の1回の応答で、次の3つを同時に（並列の関数呼び出しとして）呼ぶ。順番に待たないこと。\n"
        "   - geology_research_agent: 地域名と緯度・経度を渡し、地質の要点（地層・岩石・地形・断層など）を得る。\n"
        "   - tourism_research_agent: 地域名と緯度・経度を渡し、地質に紐づいたルートA/B/Cの候補を得る。"
        "地質の調べ物は観光側のツールが自分で行うので、地質の結果を待つ必要はない。\n"
        "   - generate_image: 地域の地形・景観を表す、文字なしのイラスト用プロンプトを作って渡す。\n"
        "2. 3つの結果がそろったら、create_map_points を1回呼び、地域名と緯度・経度を渡して地図用座標を得る。\n"
        "3. 最終回答は以下の構成で日本語でまとめる。全体で800字程度に収め、同じ内容を繰り返さない：\n"
        "   - **◆ 大地のストーリーと景観の秘密**: 地形や地質がどのように景観や文化体験に関係しているかを解説。\n"
        "   - **◆ 選べる3つの地質連動ルート案（サジェスト）**:\n"
        "     - **【ルートA】**: パノラマ絶景・地形体感（見どころ、所要時間、難易度）\n"
        "     - **【ルートB】**: 大地の恵み・湧水・段丘カフェ（見どころ、所要時間、難易度）\n"
        "     - **【ルートC】**: 歴史古道・切通し・ジオカルチャー（見どころ、所要時間、難易度）\n"
        "   - **◆ 次のステップへのご案内**: 「どのルートが気になりますか？ 例えば『ルートAを詳しく』『ルートBのカフェ巡りで行きたい』とお伝えいただければ、具体的な行程・持ち物・注意点をご案内します」と選択を促す。\n"
        "   - 画像が生成イメージであることを明記する。\n\n"
        "【ケース2：ユーザーが特定のルート（ルートA/B/C等）を選択・深掘り指定した場合】\n"
        "1. tourism_research_agent を呼び、選択されたルート（例: ルートA）の詳細な行程・タイムライン・地質見どころを取得する。\n"
        "2. create_map_points に selected_route_id（'A', 'B', 'C'など）を渡して1回呼び、そのルートに特化した地図地点を返す。\n"
        "3. 最終回答で、選択されたルートの詳しい時系列タイムライン、地質的な見どころ、移動時の注意点（足元・靴など）を丁寧に解説し、"
        "さらに「滞在時間の短縮やスポットの入れ替えも可能です」と次の対話に繋げる。"
    ),
    sub_agents=[
        geology_research_agent,
        tourism_research_agent,
    ],
    tools=[create_map_points, create_mock_map_points, generate_image],
)
