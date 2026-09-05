"""Tools used by the tourism research agent with geology-linked tour routing."""

import json
from typing import Any

from google import genai
from google.genai import types

from ..config import MODEL


def suggest_geo_tour_routes(
    location: str,
    geology_context: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    duration_hours: float | None = None,
) -> dict[str, Any]:
    """地質・地形の特徴に紐づいた複数のツアー・ルート提案（サジェスト）を返します。

    ユーザーの関心や体力に合わせて選べる3つのバリエーション（パノラマ絶景、大地の恵み・湧水、歴史探訪）
    を提示し、次の選択肢へとスムーズに繋げます。

    Args:
        location: 調査対象の地域名。
        geology_context: 地質調査エージェントから得られた地質特徴やレポートの要約。
        latitude: 中心地点または現在地の緯度。
        longitude: 中心地点または現在地の経度。
        duration_hours: 希望する観光所要時間（時間単位）。
    """
    center_lat = latitude if latitude is not None else 35.0116
    center_lng = longitude if longitude is not None else 135.7681
    loc_str = location if location and location.strip() and location != "指定なし" else "指定エリア"
    geo_str = geology_context if geology_context else "地域の段丘・地層・湧水・起伏"

    prompt = f"""
あなたは日本のジオツーリズム（大地の成り立ち×観光）の専門トラベルプランナーです。
対象地域: {loc_str} (中心緯度: {center_lat}, 中心経度: {center_lng})
地域の地質的特徴: {geo_str}

この地域の地質・地形に密接に関連する、実際に訪れることができる観光スポットと、
旅行者が選べる3つの異なる周遊ルート案（ルートA, ルートB, ルートC）を策定してください。
各スポットの座標（実在または地域内の適切な座標）を含め、以下のJSONフォーマットのみを出力してください。Markdownコードブロックは不要です。

{{
  "location": "{loc_str}",
  "region_theme": "{loc_str}の大地と観光のテーマ",
  "base_geo_story": "この地域の大地の成り立ちがどのように景観・名水・温泉・文化に影響を与えているかの解説（150文字程度）",
  "route_options": [
    {{
      "route_id": "A",
      "title": "【ルートA】ダイナミック地形・パノラマ絶景コース",
      "subtitle": "高台の展望と大地の造形美を体感するアクティブ散策",
      "geo_focus": "断層崖、隆起段丘、パノラマ眺望、地層露頭",
      "duration": "約3時間",
      "difficulty": "中級（適度な起伏あり）",
      "transportation": "徒歩（一部周遊バス）",
      "next_prompt_suggestion": "ルートAの詳細なタイムラインと見どころを教えて",
      "spots": [
        {{
          "order": 1,
          "name": "展望スポット名",
          "category": "view",
          "geo_point": "地形・地質に関する解説",
          "highlight": "おすすめの体験や見どころ",
          "stay_minutes": 40,
          "latitude": {center_lat + 0.003},
          "longitude": {center_lng + 0.003}
        }},
        {{
          "order": 2,
          "name": "自然・露頭スポット名",
          "category": "nature",
          "geo_point": "地層や岩石に関する解説",
          "highlight": "おすすめの体験や見どころ",
          "stay_minutes": 35,
          "latitude": {center_lat + 0.001},
          "longitude": {center_lng + 0.001}
        }},
        {{
          "order": 3,
          "name": "高台のカフェ・飲食店名",
          "category": "food",
          "geo_point": "地形を眺めながら休憩できる解説",
          "highlight": "名物や特産スイーツ・ランチ",
          "stay_minutes": 45,
          "latitude": {center_lat - 0.002},
          "longitude": {center_lng + 0.003}
        }}
      ]
    }},
    {{
      "route_id": "B",
      "title": "【ルートB】大地の恵み・清冽な湧水と段丘カフェコース",
      "subtitle": "地層が磨いた名水や温泉・緑陰に癒やされるのんびり周遊",
      "geo_focus": "砂礫層フィルターの湧水・伏流水・温泉地熱・段丘緑地",
      "duration": "約2時間30分",
      "difficulty": "初級（平坦で歩きやすい散策道）",
      "transportation": "徒歩",
      "next_prompt_suggestion": "ルートBの湧水カフェと癒やしプランを詳しく教えて",
      "spots": [
        {{
          "order": 1,
          "name": "湧水・親水スポット名",
          "category": "nature",
          "geo_point": "地下水・湧水の地質的仕組み",
          "highlight": "水辺の清涼感と自然景観",
          "stay_minutes": 40,
          "latitude": {center_lat - 0.001},
          "longitude": {center_lng + 0.002}
        }},
        {{
          "order": 2,
          "name": "名水仕込みのカフェ・茶房名",
          "category": "food",
          "geo_point": "清らかな水を用いた食文化の解説",
          "highlight": "名水珈琲や地場スイーツ",
          "stay_minutes": 50,
          "latitude": {center_lat - 0.003},
          "longitude": {center_lng - 0.001}
        }},
        {{
          "order": 3,
          "name": "緑の小道・親水庭園名",
          "category": "view",
          "geo_point": "水と植生が調和した地形解説",
          "highlight": "心地よい木漏れ日の散策",
          "stay_minutes": 35,
          "latitude": {center_lat + 0.001},
          "longitude": {center_lng - 0.003}
        }}
      ]
    }},
    {{
      "route_id": "C",
      "title": "【ルートC】地形と人が拓いた歴史・ジオカルチャー探訪コース",
      "subtitle": "大地を活かした古道・切通し・石造文化の歴史をたどる",
      "geo_focus": "岩盤掘削の切通し、地元の石材建築、尾根上の街道",
      "duration": "約3時間",
      "difficulty": "初〜中級（歴史街道・参道）",
      "transportation": "徒歩",
      "next_prompt_suggestion": "ルートCの歴史古道と切通しプランを詳しく教えて",
      "spots": [
        {{
          "order": 1,
          "name": "歴史古道・切通し名",
          "category": "culture",
          "geo_point": "岩盤を削った歴史的背景と地質断面",
          "highlight": "歴史の息吹と岩肌の迫力",
          "stay_minutes": 45,
          "latitude": {center_lat + 0.003},
          "longitude": {center_lng - 0.002}
        }},
        {{
          "order": 2,
          "name": "石造遺産・郷土資料館名",
          "category": "culture",
          "geo_point": "地元の石材利用や人々の暮らしの知恵",
          "highlight": "地域特有の文化・歴史展示",
          "stay_minutes": 40,
          "latitude": {center_lat - 0.002},
          "longitude": {center_lng - 0.003}
        }},
        {{
          "order": 3,
          "name": "街道名物・門前茶屋名",
          "category": "food",
          "geo_point": "街道文化と結びついた郷土の味",
          "highlight": "名物菓子とお茶の休憩",
          "stay_minutes": 35,
          "latitude": {center_lat - 0.004},
          "longitude": {center_lng + 0.001}
        }}
      ]
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
            if isinstance(data, dict) and "route_options" in data:
                # 代表マップピンを構築
                all_map_points = []
                for ro in data["route_options"]:
                    r_id = ro.get("route_id", "A")
                    for sp in ro.get("spots", []):
                        all_map_points.append({
                            "title": f"[{r_id}-{sp.get('order', 1)}] {sp.get('name')}",
                            "latitude": sp.get("latitude", center_lat),
                            "longitude": sp.get("longitude", center_lng),
                            "category": sp.get("category", "view"),
                        })
                data["map_points"] = all_map_points
                data["selection_guide"] = (
                    "お好みのルートをお選びいただけます。「ルートAを詳しく」「ルートBでのんびり行きたい」"
                    "「ルートCの歴史スポットを教えて」とお伝えいただければ、具体的な行程や見どころをご案内します。"
                )
                return data
    except Exception:
        pass

    # フォールバック（API接続不可時等でも動的生成）
    routes_data = [
        {
            "route_id": "A",
            "title": f"【ルートA】{loc_str} パノラマ絶景と大地体感コース",
            "subtitle": "高台からの見晴らしと大地の起伏を巡るアクティブ散策",
            "geo_focus": "台地と谷の高低差パノラマ、地層露頭の観察",
            "duration": "約3時間",
            "difficulty": "中級（適度な起伏あり）",
            "transportation": "徒歩",
            "next_prompt_suggestion": "ルートAの詳細なタイムラインと見どころを教えて",
            "spots": [
                {
                    "order": 1,
                    "name": f"{loc_str} パノラマ展望台",
                    "category": "view",
                    "geo_point": "段丘面から周辺の山並みや地形の起伏を一望",
                    "highlight": "爽快な見晴らしと地形パノラマ",
                    "stay_minutes": 40,
                    "latitude": round(center_lat + 0.003, 5),
                    "longitude": round(center_lng + 0.003, 5),
                },
                {
                    "order": 2,
                    "name": f"{loc_str} 地層観察ウォーキング小道",
                    "category": "nature",
                    "geo_point": "砂礫層とローム層が露出した大地の断面を間近に観察",
                    "highlight": "地層の縞模様と大地の成り立ちを学ぶ散策",
                    "stay_minutes": 35,
                    "latitude": round(center_lat + 0.001, 5),
                    "longitude": round(center_lng + 0.001, 5),
                },
                {
                    "order": 3,
                    "name": f"{loc_str} 見晴らし丘のカフェ",
                    "category": "food",
                    "geo_point": "段丘崖の縁に位置し、見下ろす街並みと風を感じる憩い場",
                    "highlight": "地元食材を使ったランチとオリジナル珈琲",
                    "stay_minutes": 45,
                    "latitude": round(center_lat - 0.002, 5),
                    "longitude": round(center_lng + 0.003, 5),
                },
            ],
        },
        {
            "route_id": "B",
            "title": f"【ルートB】{loc_str} 大地の恵み・清冽な湧水とカフェコース",
            "subtitle": "清らかな湧水と段丘の緑に癒やされるのんびり散策",
            "geo_focus": "透水層が濾過した清冽な伏流水、水辺の自然景観",
            "duration": "約2時間30分",
            "difficulty": "初級（平坦で歩きやすい散策道）",
            "transportation": "徒歩",
            "next_prompt_suggestion": "ルートBの湧水カフェと癒やしプランを詳しく教えて",
            "spots": [
                {
                    "order": 1,
                    "name": f"{loc_str} 清冽湧水池・親水スポット",
                    "category": "nature",
                    "geo_point": "不透水層の境目から湧き出る透明度抜群の清流",
                    "highlight": "水辺の清涼感と豊かな緑の鑑賞",
                    "stay_minutes": 40,
                    "latitude": round(center_lat - 0.001, 5),
                    "longitude": round(center_lng + 0.002, 5),
                },
                {
                    "order": 2,
                    "name": f"{loc_str} 名水仕込み古民家茶房",
                    "category": "food",
                    "geo_point": "名水で淹れたお茶や地元食材の甘味",
                    "highlight": "名水仕込みの和菓子とお抹茶セット",
                    "stay_minutes": 50,
                    "latitude": round(center_lat - 0.003, 5),
                    "longitude": round(center_lng - 0.001, 5),
                },
                {
                    "order": 3,
                    "name": f"{loc_str} せせらぎ緑道・里山小径",
                    "category": "view",
                    "geo_point": "湧水路に沿って整備された心地よい散策路",
                    "highlight": "小川のせせらぎを聞きながらの癒やし散歩",
                    "stay_minutes": 35,
                    "latitude": round(center_lat + 0.001, 5),
                    "longitude": round(center_lng - 0.003, 5),
                },
            ],
        },
        {
            "route_id": "C",
            "title": f"【ルートC】{loc_str} 地形と人が拓いた歴史探訪コース",
            "subtitle": "地形を活かした古道・切通しと石造遺産をたどる",
            "geo_focus": "尾根筋の歴史街道、石材文化と歴史的遺構",
            "duration": "約3時間",
            "difficulty": "初〜中級（歴史街道・神社参道）",
            "transportation": "徒歩",
            "next_prompt_suggestion": "ルートCの歴史古道と切通しプランを詳しく教えて",
            "spots": [
                {
                    "order": 1,
                    "name": f"{loc_str} 尾根筋の歴史古道",
                    "category": "culture",
                    "geo_point": "段丘の最も高い尾根を通る歴史ある主要道",
                    "highlight": "古い石仏や道標が並ぶノスタルジックな歩道",
                    "stay_minutes": 45,
                    "latitude": round(center_lat + 0.003, 5),
                    "longitude": round(center_lng - 0.002, 5),
                },
                {
                    "order": 2,
                    "name": f"{loc_str} 郷土石造遺産・文化資料館",
                    "category": "culture",
                    "geo_point": "地元の石材を使った建築や人々の営みの記録",
                    "highlight": "大地と人々の知恵を結ぶ企画展示",
                    "stay_minutes": 40,
                    "latitude": round(center_lat - 0.002, 5),
                    "longitude": round(center_lng - 0.003, 5),
                },
                {
                    "order": 3,
                    "name": f"{loc_str} 門前銘菓・甘味処",
                    "category": "food",
                    "geo_point": "古道沿いで昔から旅人を迎えてきた老舗の味",
                    "highlight": "名物餅と香ばしいお茶で一服",
                    "stay_minutes": 35,
                    "latitude": round(center_lat - 0.004, 5),
                    "longitude": round(center_lng + 0.001, 5),
                },
            ],
        },
    ]

    all_map_points = []
    for ro in routes_data:
        r_id = ro["route_id"]
        for sp in ro["spots"]:
            all_map_points.append({
                "title": f"[{r_id}-{sp['order']}] {sp['name']}",
                "latitude": sp["latitude"],
                "longitude": sp["longitude"],
                "category": sp["category"],
            })

    return {
        "location": loc_str,
        "region_theme": f"{loc_str}の大地と観光の調和",
        "base_geo_story": f"{loc_str}の地形と地層は、独自の景観や豊かな水・文化を育んできました。",
        "route_options": routes_data,
        "map_points": all_map_points,
        "selection_guide": (
            "お好みのルートをお選びいただけます。「ルートAを詳しく」「ルートBでのんびり行きたい」"
            "「ルートCの歴史スポットを教えて」とお伝えいただければ、具体的な行程や見どころをご案内します。"
        ),
    }


def plan_tour_route(
    location: str,
    latitude: float | None = None,
    longitude: float | None = None,
    theme: str | None = None,
    duration_hours: float | None = None,
    transportation: str | None = "徒歩",
    geology_context: str | None = None,
    selected_route_id: str | None = "A",
) -> dict[str, Any]:
    """特定の選択されたルート（ルートA/B/C等）について詳細な行程・タイムラインを策定します。

    Args:
        location: 調査対象の地域名。
        latitude: 中心地点または現在地の緯度。
        longitude: 中心地点または現在地の経度。
        theme: 観光のテーマ。
        duration_hours: 想定する観光所要時間。
        transportation: 主な移動手段。
        geology_context: 地質特徴の要約。
        selected_route_id: 選択されたルートID（"A", "B", "C"）。
    """
    multi = suggest_geo_tour_routes(
        location=location,
        geology_context=geology_context,
        latitude=latitude,
        longitude=longitude,
        duration_hours=duration_hours,
    )

    route_key = (
        selected_route_id.upper()
        if selected_route_id and selected_route_id.upper() in ["A", "B", "C"]
        else "A"
    )

    matched = next(
        (r for r in multi["route_options"] if r.get("route_id") == route_key),
        multi["route_options"][0],
    )

    transport = transportation if transportation else matched.get("transportation", "徒歩")
    spots = matched.get("spots", [])

    destinations = []
    map_points = []
    itinerary = []

    current_hour = 10
    current_minute = 0

    for idx, spot in enumerate(spots):
        order = idx + 1
        stay_mins = int(spot.get("stay_minutes", 40))
        transit_mins = 15 if idx > 0 else 0

        current_minute += transit_mins
        if current_minute >= 60:
            current_hour += current_minute // 60
            current_minute %= 60
        arrival_time = f"{current_hour:02d}:{current_minute:02d}"

        current_minute += stay_mins
        if current_minute >= 60:
            current_hour += current_minute // 60
            current_minute %= 60
        departure_time = f"{current_hour:02d}:{current_minute:02d}"

        dest_info = {
            "order": order,
            "name": spot.get("name"),
            "category": spot.get("category", "view"),
            "geo_point": spot.get("geo_point", ""),
            "highlight": spot.get("highlight", ""),
            "stay_minutes": stay_mins,
            "latitude": spot.get("latitude"),
            "longitude": spot.get("longitude"),
        }
        destinations.append(dest_info)

        is_last = idx == len(spots) - 1
        next_transit = (
            "最寄り駅・交通拠点へ移動しゴール"
            if is_last
            else f"{transport}で約10〜15分移動"
        )

        itinerary.append({
            "step": order,
            "time_window": f"{arrival_time} - {departure_time}",
            "spot_name": spot.get("name"),
            "geo_story": spot.get("geo_point", ""),
            "activity": f"{spot.get('highlight', '')}（地質見どころ: {spot.get('geo_point', '')}）",
            "next_transit": next_transit,
        })

        map_points.append({
            "title": f"[{order}] {spot.get('name')}",
            "latitude": spot.get("latitude"),
            "longitude": spot.get("longitude"),
            "category": spot.get("category", "view"),
        })

    travel_advice = [
        f"推奨移動手段: {transport}（コース難易度: {matched.get('difficulty', '初〜中級')}）。",
        "地質の観察スポットや展望台周辺は未舗装の歩道や階段もあるため、歩きやすい靴でお越しください。",
        "天候や時間の都合に合わせた立ち寄り先の増減・変更も可能です。",
    ]

    return {
        "location": multi.get("location"),
        "selected_route_id": route_key,
        "route_title": matched.get("title"),
        "subtitle": matched.get("subtitle"),
        "geo_focus": matched.get("geo_focus"),
        "summary": f"{multi.get('base_geo_story', '')} {matched.get('subtitle', '')}",
        "total_duration": matched.get("duration"),
        "difficulty": matched.get("difficulty"),
        "transportation": transport,
        "destinations": destinations,
        "itinerary": itinerary,
        "travel_advice": travel_advice,
        "map_points": map_points,
        "recommended_spots": [d["name"] for d in destinations],
        "sample_plan": " -> ".join([str(d["name"]) for d in destinations]),
    }


def get_tourism_report(
    location: str,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict[str, Any]:
    """指定地域の観光調査・ルートレポートを返します。"""
    multi = suggest_geo_tour_routes(location, None, latitude, longitude)
    single = plan_tour_route(location, latitude, longitude, selected_route_id="A")

    return {
        **single,
        "route_options": multi.get("route_options", []),
        "region_theme": multi.get("region_theme", ""),
        "base_geo_story": multi.get("base_geo_story", ""),
        "selection_guide": multi.get("selection_guide", ""),
    }


def get_mock_tourism_report(
    location: str,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict[str, Any]:
    """後方互換用エイリアス"""
    return get_tourism_report(location, latitude, longitude)
