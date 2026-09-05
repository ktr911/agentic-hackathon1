"""Root agent definition loaded by the ADK CLI."""

import os
from uuid import uuid4

from google import genai
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.tools import ToolContext
from google.genai import types


def get_mock_geology_report(
    location: str,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict[str, object]:
    """指定地域のモック地質調査レポートを返します。

    Args:
        location: 調査対象の地域名。指定がなければ「指定なし」。
        latitude: クライアントから渡された中心地点の緯度。
        longitude: クライアントから渡された中心地点の経度。
    """
    center_latitude = latitude if latitude is not None else 35.2324
    center_longitude = longitude if longitude is not None else 139.1069
    return {
        "is_mock": True,
        "location": location,
        "summary": "丘陵地を中心に火山性堆積物が分布している想定です。",
        "findings": [
            "表層はローム質土を想定",
            "一部に砂礫層が存在する想定",
            "詳細判断には現地ボーリング調査が必要",
        ],
        "map_points": [
            {
                "title": "表層観察ポイント（モック）",
                "latitude": center_latitude,
                "longitude": center_longitude,
                "category": "geology",
            },
            {
                "title": "砂礫層想定ポイント（モック）",
                "latitude": center_latitude + 0.004,
                "longitude": center_longitude + 0.006,
                "category": "geology",
            },
        ],
    }


def get_mock_tourism_report(
    location: str,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict[str, object]:
    """指定地域のモック観光調査レポートを返します。

    Args:
        location: 調査対象の地域名。指定がなければ「指定なし」。
        latitude: クライアントから渡された中心地点の緯度。
        longitude: クライアントから渡された中心地点の経度。
    """
    center_latitude = latitude if latitude is not None else 35.0116
    center_longitude = longitude if longitude is not None else 135.7681
    return {
        "is_mock": True,
        "location": location,
        "summary": "自然散策と地域文化を組み合わせた観光プランの想定です。",
        "recommended_spots": [
            "地域の景観を楽しめる展望スポット",
            "郷土資料を扱う文化施設",
            "地元食材を楽しめる飲食エリア",
        ],
        "sample_plan": "午前に散策、昼に郷土料理、午後に文化施設を巡ります。",
        "map_points": [
            {
                "title": "景観スポット（モック）",
                "latitude": center_latitude,
                "longitude": center_longitude,
                "category": "view",
            },
            {
                "title": "文化施設（モック）",
                "latitude": center_latitude + 0.003,
                "longitude": center_longitude - 0.004,
                "category": "culture",
            },
            {
                "title": "飲食エリア（モック）",
                "latitude": center_latitude - 0.004,
                "longitude": center_longitude + 0.003,
                "category": "food",
            },
        ],
    }


def create_mock_map_points(
    location: str,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict[str, object]:
    """地質・観光のモック調査地点を、クライアント表示用にまとめます。

    Args:
        location: 調査対象の地域名。
        latitude: クライアントから渡された中心地点の緯度。
        longitude: クライアントから渡された中心地点の経度。
    """
    geology = get_mock_geology_report(location, latitude, longitude)
    tourism = get_mock_tourism_report(location, latitude, longitude)
    return {
        "is_mock": True,
        "location": location,
        "map_points": [
            *geology["map_points"],
            *tourism["map_points"],
        ],
    }


MODEL = os.getenv("ADK_MODEL", "gemini-3.7-flash")
IMAGE_MODEL = os.getenv("ADK_IMAGE_MODEL", "gemini-3.1-flash-image")


async def generate_image(prompt: str, tool_context: ToolContext) -> dict[str, object]:
    """画像を生成し、現在のADKセッションへartifactとして保存します。

    Args:
        prompt: 生成したい画像の具体的な説明。
        tool_context: ADKが注入する現在のツール実行コンテキスト。
    """
    client = genai.Client()
    try:
        response = await client.aio.models.generate_content(
            model=IMAGE_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            ),
        )
    finally:
        await client.aio.aclose()

    image_part = next(
        (part for part in response.parts if part.inline_data is not None),
        None,
    )
    if image_part is None or image_part.inline_data is None:
        return {
            "status": "error",
            "message": "画像モデルから画像データが返されませんでした。",
        }

    mime_type = image_part.inline_data.mime_type or "image/png"
    extension = "jpg" if mime_type == "image/jpeg" else "png"
    filename = f"generated-{uuid4().hex[:12]}.{extension}"
    version = await tool_context.save_artifact(filename, image_part)

    return {
        "status": "success",
        "filename": filename,
        "version": version,
        "mime_type": mime_type,
        "is_generated": True,
    }

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

app = App(name="agent", root_agent=root_agent)
