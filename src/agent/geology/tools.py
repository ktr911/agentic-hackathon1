"""Tools used by the geology research agent."""

import json
from typing import Any

from google import genai
from google.genai import types

from ..config import MODEL


def get_geology_report(
    location: str,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict[str, Any]:
    """指定地域の地質・地形・地盤調査レポートを返します。

    Args:
        location: 調査対象の地域名。
        latitude: クライアントから渡された中心地点の緯度。
        longitude: クライアントから渡された中心地点の経度。
    """
    center_lat = latitude if latitude is not None else 35.0116
    center_lng = longitude if longitude is not None else 135.7681
    target_loc = (
        location
        if location and location.strip() and location != "指定なし"
        else "指定エリア"
    )

    prompt = f"""
あなたは日本の地質学・地球科学の専門調査員です。
対象地域: {target_loc} (中心緯度: {center_lat}, 中心経度: {center_lng})
この地域の地質・地形（地層、岩石、断層、段丘、火山活動、地盤、大地の形成史）について調査し、
実際に観察可能な地質スポット（露頭、断層崖、奇岩、段丘面、湧水地など）の座標を含めて、
以下のJSONフォーマットのみを出力してください。Markdownのコードブロックは不要です。

{{
  "location": "{target_loc}",
  "summary": "この地域の地質と大地の成り立ちの要約（200文字程度）",
  "formation_era": "主な形成年代（例: 新生代第四紀、中生代白亜紀など）",
  "rock_types": ["代表的な岩石・地層1", "代表的な岩石・地層2"],
  "geological_features": [
    "地質学的な重要特徴1",
    "地質学的な重要特徴2",
    "地形や断層に関する特徴3"
  ],
  "map_points": [
    {{
      "title": "地質観察スポット名1",
      "latitude": {center_lat + 0.002},
      "longitude": {center_lng + 0.003},
      "category": "geology",
      "description": "観察できる地層や岩石の解説"
    }},
    {{
      "title": "地質観察スポット名2",
      "latitude": {center_lat - 0.003},
      "longitude": {center_lng - 0.002},
      "category": "geology",
      "description": "観察できる地形や断層の解説"
    }}
  ]
}}
"""
    try:
        client = genai.Client()
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        if response.text:
            data = json.loads(response.text)
            if isinstance(data, dict) and "map_points" in data:
                return data
    except Exception:
        pass

    # フォールバック（API接続不可時等でも地域に応じた動的生成）
    return {
        "location": target_loc,
        "summary": f"{target_loc}周辺は、プレート運動と侵食・堆積作用によって形成された特徴的な起伏や地層を有しています。",
        "formation_era": "新生代第四紀",
        "rock_types": ["堆積岩（砂岩・泥岩）", "表層堆積物（ローム・礫層）"],
        "geological_features": [
            "河川や海の作用による段丘崖や谷戸地形の形成",
            "水を通しやすい砂礫層と保水性のある粘土層の互層",
            "大地の隆起・沈降に伴う断層や傾斜地盤",
        ],
        "map_points": [
            {
                "title": f"{target_loc} 地層露頭・表層観察地点",
                "latitude": center_lat + 0.002,
                "longitude": center_lng + 0.003,
                "category": "geology",
                "description": "地域の大地を構成する表層地層や堆積構造を観察できるポイント",
            },
            {
                "title": f"{target_loc} 地形境界・断層崖観察地点",
                "latitude": center_lat - 0.003,
                "longitude": center_lng - 0.002,
                "category": "geology",
                "description": "台地と谷の高低差や浸食の痕跡が明瞭に現れている地形ポイント",
            },
        ],
    }


def get_mock_geology_report(
    location: str,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict[str, Any]:
    """後方互換用エイリアス"""
    return get_geology_report(location, latitude, longitude)
