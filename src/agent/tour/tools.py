"""Tools used by the tourism research agent with geology-linked tour routing."""

import json
import logging
from typing import Any

from google import genai
from google.genai import types

from ..config import MODEL, MODEL_LOCATION

logger = logging.getLogger(__name__)


def suggest_geo_tour_routes(
    location: str,
    geology_context: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    duration_hours: float | None = None,
) -> dict[str, Any]:
    """地質・地形の特徴に紐づいた複数のツアー・ルート提案（サジェスト）を返します。

    ブラタモリ的な大地の秘密（なぜなに解説）、高低差を考慮した疲れない巡り順、
    地質ゆかりのジオフード、＋30分の寄り道サジェストを含めて提示し、
    ユーザーが興味に合わせてルートを選択できるようにします。

    Args:
        location: 調査対象の地域名。
        geology_context: 地質調査エージェントから得られた地質特徴やレポートの要約。
        latitude: 中心地点または現在地の緯度。
        longitude: 中心地点または現在地の経度。
        duration_hours: 希望する観光所要時間（時間単位）。
    """
    center_lat = latitude if latitude is not None else 35.0116
    center_lng = longitude if longitude is not None else 135.7681
    loc_str = (
        location
        if location and location.strip() and location != "指定なし"
        else "指定エリア"
    )
    geo_str = geology_context if geology_context else "地域の段丘・地層・湧水・起伏"

    prompt = f"""
あなたは日本のジオツーリズム（大地の成り立ち×観光・まち歩き）の専門トラベルプランナーです。
対象地域: {loc_str} (中心緯度: {center_lat}, 中心経度: {center_lng})
地域の地質的特徴: {geo_str}

この地域の地質・地形を活かし、旅行者がワクワクして選べる3つの異なる周遊ルート案（ルートA, ルートB, ルートC）を策定してください。
ブラタモリ的な『大地のなぜなに（雑学）』、高低差を考慮した疲れない歩行設計（下り坂や平坦基調）、地質の恵みグルメ（ジオフード）、＋30分の寄り道スポット、写真撮影のベストアングルを含めて、
以下のJSONフォーマットのみを出力してください。Markdownコードブロックは不要です。

{{
  "location": "{loc_str}",
  "region_theme": "{loc_str}の大地と観光のテーマ",
  "base_geo_story": "この地域の大地の成り立ちがどのように景観・名水・温泉・文化に影響を与えているかの解説（150文字程度）",
  "route_options": [
    {{
      "route_id": "A",
      "title": "【ルートA】ダイナミック地形・パノラマ絶景コース",
      "subtitle": "高台からの見晴らしと大地の起伏を巡るパノラマ散策",
      "geo_focus": "断層崖、隆起段丘、パノラマ眺望、地層露頭",
      "elevation_strategy": "登りはバスで高台へ、散策は緩やかな下り坂中心の省エネ設計（歩行負荷: ★★☆）",
      "geo_story_highlight": "大地のなぜなに: なぜここに大パノラマが？ 太古の隆起運動と河川の侵食が造り出した奇跡の断崖地形",
      "geo_gourmet": "高台テラスで味わう地場野菜ランチ＆絶景焙煎珈琲",
      "detour_suggestion": "＋30分の寄り道: 時間があれば徒歩5分の『隠れ地層展望ベンチ』にも立ち寄り可能",
      "photo_tip": "展望テラスから南西向き：午後の斜光で断層崖の陰影が際立ち立体的な写真が撮れます",
      "duration": "約3時間",
      "difficulty": "中級（下り基調・適度な散策）",
      "transportation": "周遊バス＋徒歩（下り坂中心）",
      "next_prompt_suggestion": "ルートAの詳細なタイムラインと見どころを教えて",
      "spots": [
        {{
          "order": 1,
          "name": "高台パノラマ展望スポット名",
          "category": "view",
          "terrain": "段丘最頂部（標高差を一望）",
          "geo_point": "地形・地質に関する解説",
          "geo_trivia": "なぜここに展望台？ 浸食に耐えた硬い岩盤が山頂部に残ったため",
          "highlight": "大地のスケールを体感するパノラマ眺望",
          "stay_minutes": 40,
          "latitude": {center_lat + 0.003},
          "longitude": {center_lng + 0.003}
        }},
        {{
          "order": 2,
          "name": "大地の露頭・地層ウォーキング小道名",
          "category": "nature",
          "terrain": "緩やかな下り坂の遊歩道",
          "geo_point": "地層や岩石に関する解説",
          "geo_trivia": "縞模様の正体: 数万年前の火山噴火と河川堆積が交互に積み重なった地層の年輪",
          "highlight": "地層を間近に観察しながらの下り坂ウォーク",
          "stay_minutes": 35,
          "latitude": {center_lat + 0.001},
          "longitude": {center_lng + 0.001}
        }},
        {{
          "order": 3,
          "name": "絶景見晴らしカフェ・飲食店名",
          "category": "food",
          "terrain": "中腹の平坦地（休憩に最適）",
          "geo_point": "地形を眺めながら休憩できる解説",
          "geo_trivia": "地形の恵み: 地下深くから引いたミネラル豊富な井戸水を使用したドリンク",
          "highlight": "絶景スイーツとリフレッシュタイム",
          "stay_minutes": 45,
          "latitude": {center_lat - 0.002},
          "longitude": {center_lng + 0.003}
        }}
      ]
    }},
    {{
      "route_id": "B",
      "title": "【ルートB】大地の恵み・清冽な湧水と段丘カフェコース",
      "subtitle": "砂礫層が磨いた名水と木陰の小道に癒やされるのんびり周遊",
      "geo_focus": "砂礫層フィルターの湧水・伏流水・温泉地熱・段丘下の平坦緑道",
      "elevation_strategy": "段丘崖下のほぼ完全フラットな木陰ルート（階段なし・歩行負荷: ★☆☆）",
      "geo_story_highlight": "大地のなぜなに: なぜここに湧水が？ 水を通しやすい砂礫層と通さない粘土層の境目から数十年前の雨水が湧出",
      "geo_gourmet": "名水仕込みの手打ち蕎麦＆湧水水出しアイスコーヒー",
      "detour_suggestion": "＋30分の寄り道: 足湯や冷水手水のある『湧水親水小公園』でのんびり涼むのがおすすめ",
      "photo_tip": "湧水池の木道から水面越しに撮影：透明度抜群の水中植物と木漏れ日が美しく映えます",
      "duration": "約2時間30分",
      "difficulty": "初級（平坦・バリアフリー散策）",
      "transportation": "徒歩（平坦小道）",
      "next_prompt_suggestion": "ルートBの湧水カフェと癒やしプランを詳しく教えて",
      "spots": [
        {{
          "order": 1,
          "name": "清冽湧水池・親水スポット名",
          "category": "nature",
          "terrain": "段丘崖下の平坦地（湧水帯）",
          "geo_point": "地下水・湧水の地質的仕組み",
          "geo_trivia": "天然のフィルター: 富士・箱根や周辺山地の火山灰層を潜り抜けた極上の軟水",
          "highlight": "湧水池の清涼感とマイナスイオン",
          "stay_minutes": 40,
          "latitude": {center_lat - 0.001},
          "longitude": {center_lng + 0.002}
        }},
        {{
          "order": 2,
          "name": "名水仕込みの古民家カフェ・茶房名",
          "category": "food",
          "terrain": "水辺沿いの平坦な古民家街",
          "geo_point": "清らかな水を用いた食文化の解説",
          "geo_trivia": "名水の味: 硬度が低く出汁やコーヒーの香りを最大限に引き出す湧水の恩恵",
          "highlight": "名水珈琲と季節の甘味セット",
          "stay_minutes": 50,
          "latitude": {center_lat - 0.003},
          "longitude": {center_lng - 0.001}
        }},
        {{
          "order": 3,
          "name": "せせらぎ親水緑道・里山小道名",
          "category": "view",
          "terrain": "水路に沿ったフラットな緑道",
          "geo_point": "水と植生が調和した地形解説",
          "geo_trivia": "生活と地形: 段丘の湧水を水田や生活用水に引くために江戸期に拓かれた水路跡",
          "highlight": "せせらぎの音を聞きながらの癒やし歩き",
          "stay_minutes": 35,
          "latitude": {center_lat + 0.001},
          "longitude": {center_lng - 0.003}
        }}
      ]
    }},
    {{
      "route_id": "C",
      "title": "【ルートC】地形と人が拓いた歴史・ジオカルチャー探訪コース",
      "subtitle": "岩盤を削った切通しや尾根の古道から人々の知恵をたどる",
      "geo_focus": "切通し（人工地層断面）、石造文化、尾根筋の要害古道",
      "elevation_strategy": "尾根筋の緩やかなアップダウンで歴史の起伏を体感（歩行負荷: ★★☆）",
      "geo_story_highlight": "大地のなぜなに: なぜこの道が作られた？ 水害の多い低地を避け、硬い砂岩の尾根を切り拓いて交通路を確保した先人の知恵",
      "geo_gourmet": "街道筋の名物力餅＆石臼挽き抹茶セット",
      "detour_suggestion": "＋30分の寄り道: 古代の石切り場跡を望む『地学モニュメント広場』への寄り道がおすすめ",
      "photo_tip": "切通しの両岸を見上げるローアングル：垂直に削られた岩肌と苔の陰影が大迫力で撮れます",
      "duration": "約3時間",
      "difficulty": "初〜中級（石畳・歴史小道）",
      "transportation": "徒歩（一部石畳道）",
      "next_prompt_suggestion": "ルートCの歴史古道と切通しプランを詳しく教えて",
      "spots": [
        {{
          "order": 1,
          "name": "歴史の切通し・岩壁古道名",
          "category": "culture",
          "terrain": "岩盤を削り抜いた切通し道",
          "geo_point": "岩盤を削った歴史的背景と地質断面",
          "geo_trivia": "石工のノミ跡: 固すぎず柔らかすぎない絶妙な凝灰質砂岩だからこそ人力で開通できた",
          "highlight": "垂直な岩肌に挟まれた歴史古道の迫力",
          "stay_minutes": 45,
          "latitude": {center_lat + 0.003},
          "longitude": {center_lng - 0.002}
        }},
        {{
          "order": 2,
          "name": "石造遺産・郷土資料館名",
          "category": "culture",
          "terrain": "門前町の緩やかな坂道",
          "geo_point": "地元の石材利用や人々の暮らしの知恵",
          "geo_trivia": "石材の適材適所: 寺社の石段や土台に使われた地元特有の石材（鎌倉石・安山岩等）の歴史",
          "highlight": "地域特有の石材文化と歴史展示",
          "stay_minutes": 40,
          "latitude": {center_lat - 0.002},
          "longitude": {center_lng - 0.003}
        }},
        {{
          "order": 3,
          "name": "街道名物・門前茶屋名",
          "category": "food",
          "terrain": "街道沿いの宿場町エリア",
          "geo_point": "街道文化と結びついた郷土の味",
          "geo_trivia": "旅人のオアシス: 峠越えの難所を越えた旅人を迎えた歴史ある茶屋の立地",
          "highlight": "香ばしい名物焼き団子とお茶で一服",
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
        client = genai.Client(vertexai=True, location=MODEL_LOCATION)
        try:
            response = client.models.generate_content(
                model=MODEL.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
        finally:
            client.close()
        if response.text:
            data = json.loads(response.text)
            if isinstance(data, dict) and "route_options" in data:
                all_map_points = []
                for ro in data["route_options"]:
                    r_id = ro.get("route_id", "A")
                    for sp in ro.get("spots", []):
                        all_map_points.append(
                            {
                                "title": f"[{r_id}-{sp.get('order', 1)}] {sp.get('name')}",
                                "latitude": sp.get("latitude", center_lat),
                                "longitude": sp.get("longitude", center_lng),
                                "category": sp.get("category", "view"),
                            }
                        )
                data["map_points"] = all_map_points
                data["selection_guide"] = (
                    "お好みのルートをお選びいただけます。「ルートAを詳しく」「ルートBでのんびり行きたい」"
                    "「ルートCの歴史スポットを教えて」とお伝えいただければ、具体的な行程や見どころをご案内します。"
                )
                return data
    except Exception as exc:  # noqa: BLE001 - フォールバックを返して対話を継続する
        logger.warning(
            "ルート候補の動的生成に失敗したためフォールバックを使用します: %s", exc
        )

    # フォールバック（API未設定・オフライン時等でも地域に応じた動的生成）
    routes_data = [
        {
            "route_id": "A",
            "title": f"【ルートA】{loc_str} パノラマ絶景と大地体感コース",
            "subtitle": "高台からの見晴らしと大地の起伏を巡るパノラマ散策",
            "geo_focus": "断層崖、隆起段丘、パノラマ眺望、地層露頭",
            "elevation_strategy": "登りはバスで高台へ、散策は緩やかな下り坂中心の省エネ設計（歩行負荷: ★★☆）",
            "geo_story_highlight": f"大地のなぜなに: なぜ{loc_str}に大パノラマが？ 太古の断層隆起と浸食作用が生んだ絶景",
            "geo_gourmet": "見晴らしカフェの地場野菜ランチ＆絶景焙煎珈琲",
            "detour_suggestion": "＋30分の寄り道: 徒歩5分の『大地の展望テラスベンチ』で夕景鑑賞もおすすめ",
            "photo_tip": "展望台から南西向き：午後の光で地形の陰影が際立ちベストショットが撮れます",
            "duration": "約3時間",
            "difficulty": "中級（下り坂メインで快適）",
            "transportation": "バス＋徒歩（下り坂中心）",
            "next_prompt_suggestion": "ルートAの詳細なタイムラインと見どころを教えて",
            "spots": [
                {
                    "order": 1,
                    "name": f"{loc_str} パノラマ展望台",
                    "category": "view",
                    "terrain": "段丘最頂部（標高差を一望）",
                    "geo_point": "段丘面から周辺の山並みや地形の起伏を一望",
                    "geo_trivia": "なぜここに展望台？ 浸食に耐えた硬い岩盤が山頂部に残ったため",
                    "highlight": "爽快な見晴らしと地形パノラマ",
                    "stay_minutes": 40,
                    "latitude": round(center_lat + 0.003, 5),
                    "longitude": round(center_lng + 0.003, 5),
                },
                {
                    "order": 2,
                    "name": f"{loc_str} 地層観察ウォーキング小道",
                    "category": "nature",
                    "terrain": "緩やかな下り坂の遊歩道",
                    "geo_point": "砂礫層とローム層が露出した大地の断面を間近に観察",
                    "geo_trivia": "地層の年輪: 火山噴火の火山灰と河川堆積が重なった数十万年の歴史",
                    "highlight": "地層の縞模様と大地の成り立ちを学ぶ散策",
                    "stay_minutes": 35,
                    "latitude": round(center_lat + 0.001, 5),
                    "longitude": round(center_lng + 0.001, 5),
                },
                {
                    "order": 3,
                    "name": f"{loc_str} 見晴らし丘のカフェ",
                    "category": "food",
                    "terrain": "中腹の平坦地（休憩に最適）",
                    "geo_point": "段丘崖の縁に位置し、見下ろす街並みと風を感じる憩い場",
                    "geo_trivia": "大地の恵み: 地下水脈から汲み上げた軟水で淹れるオリジナル珈琲",
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
            "subtitle": "砂礫層が磨いた名水と段丘下の緑道に癒やされるのんびり散策",
            "geo_focus": "砂礫層フィルターの湧水・伏流水・温泉地熱・平坦な親水緑道",
            "elevation_strategy": "段丘崖下のほぼ完全フラットな木陰ルート（階段なし・歩行負荷: ★☆☆）",
            "geo_story_highlight": "大地のなぜなに: なぜここに湧水が？ 透水性の砂礫層と不透水の粘土層の境目から数十年前の雨水が噴出",
            "geo_gourmet": "名水仕込みの手打ち蕎麦＆湧水水出し珈琲",
            "detour_suggestion": "＋30分の寄り道: 足湯や冷水手水のある『湧水親水小公園』でのんびり涼むのがおすすめ",
            "photo_tip": "湧水池の木道から水面越しに撮影：透明度抜群の水中植物と木漏れ日が美しく映えます",
            "duration": "約2時間30分",
            "difficulty": "初級（平坦・バリアフリー散策）",
            "transportation": "徒歩（平坦小道）",
            "next_prompt_suggestion": "ルートBの湧水カフェと癒やしプランを詳しく教えて",
            "spots": [
                {
                    "order": 1,
                    "name": f"{loc_str} 清冽湧水池・親水スポット",
                    "category": "nature",
                    "terrain": "段丘崖下の平坦地（湧水帯）",
                    "geo_point": "不透水層の境目から湧き出る透明度抜群の清流",
                    "geo_trivia": "天然のフィルター: 地層が長い年月をかけて不純物をろ過したミネラル水",
                    "highlight": "水辺の清涼感と豊かな緑の鑑賞",
                    "stay_minutes": 40,
                    "latitude": round(center_lat - 0.001, 5),
                    "longitude": round(center_lng + 0.002, 5),
                },
                {
                    "order": 2,
                    "name": f"{loc_str} 名水仕込み古民家茶房",
                    "category": "food",
                    "terrain": "水辺沿いの平坦な古民家街",
                    "geo_point": "名水で淹れたお茶や地元食材の甘味",
                    "geo_trivia": "名水の味: 硬度が低く出汁やコーヒーの香りを最大限に引き出す湧水の恩恵",
                    "highlight": "名水仕込みの和菓子とお抹茶セット",
                    "stay_minutes": 50,
                    "latitude": round(center_lat - 0.003, 5),
                    "longitude": round(center_lng - 0.001, 5),
                },
                {
                    "order": 3,
                    "name": f"{loc_str} せせらぎ緑道・里山小径",
                    "category": "view",
                    "terrain": "水路に沿ったフラットな緑道",
                    "geo_point": "湧水路に沿って整備された心地よい散策路",
                    "geo_trivia": "生活と地形: 段丘の湧水を農業や生活に引くために古くから拓かれた水路跡",
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
            "subtitle": "岩盤を削った切通しや尾根筋の古道から人々の知恵をたどる",
            "geo_focus": "尾根筋の歴史街道、石材文化と歴史的遺構",
            "elevation_strategy": "尾根筋の緩やかなアップダウンで歴史の起伏を体感（歩行負荷: ★★☆）",
            "geo_story_highlight": "大地のなぜなに: なぜこの道が作られた？ 氾濫しやすい低地を避け、地盤の硬い段丘尾根を通した古代の知恵",
            "geo_gourmet": "街道筋の名物力餅＆石臼挽き抹茶セット",
            "detour_suggestion": "＋30分の寄り道: 古代の石切り場跡を望む『地学モニュメント広場』への寄り道がおすすめ",
            "photo_tip": "切通しの両岸を見上げるローアングル：垂直に削られた岩肌と苔の陰影が大迫力で撮れます",
            "duration": "約3時間",
            "difficulty": "初〜中級（歴史街道・神社参道）",
            "transportation": "徒歩（一部石畳道）",
            "next_prompt_suggestion": "ルートCの歴史古道と切通しプランを詳しく教えて",
            "spots": [
                {
                    "order": 1,
                    "name": f"{loc_str} 尾根筋の歴史古道",
                    "category": "culture",
                    "terrain": "岩盤を削り抜いた切通し道",
                    "geo_point": "段丘の最も高い尾根を通る歴史ある主要道",
                    "geo_trivia": "石工の知恵: 掘削に適した砂岩層を見極めて人力で切り拓いた要衝",
                    "highlight": "古い石仏や道標が並ぶノスタルジックな歩道",
                    "stay_minutes": 45,
                    "latitude": round(center_lat + 0.003, 5),
                    "longitude": round(center_lng - 0.002, 5),
                },
                {
                    "order": 2,
                    "name": f"{loc_str} 郷土石造遺産・文化資料館",
                    "category": "culture",
                    "terrain": "門前町の緩やかな坂道",
                    "geo_point": "地元の石材を使った建築や人々の営みの記録",
                    "geo_trivia": "石材の歴史: 寺社仏閣の礎石や石垣に使われた地元石材の採掘の歴史",
                    "highlight": "大地と人々の知恵を結ぶ企画展示",
                    "stay_minutes": 40,
                    "latitude": round(center_lat - 0.002, 5),
                    "longitude": round(center_lng - 0.003, 5),
                },
                {
                    "order": 3,
                    "name": f"{loc_str} 門前銘菓・甘味処",
                    "category": "food",
                    "terrain": "街道沿いの宿場町エリア",
                    "geo_point": "古道沿いで昔から旅人を迎えてきた老舗の味",
                    "geo_trivia": "旅人のオアシス: 峠越えの難所を越えた旅人を迎えた歴史ある茶屋の立地",
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
            all_map_points.append(
                {
                    "title": f"[{r_id}-{sp['order']}] {sp['name']}",
                    "latitude": sp["latitude"],
                    "longitude": sp["longitude"],
                    "category": sp["category"],
                }
            )

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

    ブラタモリ的な大地のなぜなに解説、区間ごとの高低差（上り/下り/平坦）、
    おすすめ写真アングル、＋30分の寄り道プランを含めた詳細な旅程を返します。

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

    transport = (
        transportation if transportation else matched.get("transportation", "徒歩")
    )
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
            "terrain": spot.get("terrain", "平坦"),
            "geo_point": spot.get("geo_point", ""),
            "geo_trivia": spot.get("geo_trivia", ""),
            "highlight": spot.get("highlight", ""),
            "stay_minutes": stay_mins,
            "latitude": spot.get("latitude"),
            "longitude": spot.get("longitude"),
        }
        destinations.append(dest_info)

        is_last = idx == len(spots) - 1
        transit_desc = (
            "最寄り駅・交通拠点へ移動しゴール"
            if is_last
            else f"{transport}で約10〜15分移動（{spot.get('terrain', '快適な道')}）"
        )

        itinerary.append(
            {
                "step": order,
                "time_window": f"{arrival_time} - {departure_time}",
                "spot_name": spot.get("name"),
                "terrain": spot.get("terrain", "平坦"),
                "geo_trivia": spot.get("geo_trivia", ""),
                "activity": f"{spot.get('highlight', '')}（地質ポイント: {spot.get('geo_point', '')}）",
                "next_transit": transit_desc,
            }
        )

        map_points.append(
            {
                "title": f"[{order}] {spot.get('name')}",
                "latitude": spot.get("latitude"),
                "longitude": spot.get("longitude"),
                "category": spot.get("category", "view"),
            }
        )

    travel_advice = [
        f"高低差・歩行設計: {matched.get('elevation_strategy', '歩きやすいルート設計です')}",
        f"おすすめ撮影アングル: {matched.get('photo_tip', '見晴らしの良い場所からのパノラマ撮影がおすすめ')}",
        f"地質ゆかりの名物（ジオフード）: {matched.get('geo_gourmet', '地場の名水・特産品をお楽しみください')}",
        f"時間に余裕がある時の寄り道（＋30分）: {matched.get('detour_suggestion', '周辺の散策小径への寄り道も可能です')}",
    ]

    return {
        "location": multi.get("location"),
        "selected_route_id": route_key,
        "route_title": matched.get("title"),
        "subtitle": matched.get("subtitle"),
        "geo_focus": matched.get("geo_focus"),
        "elevation_strategy": matched.get("elevation_strategy"),
        "geo_story_highlight": matched.get("geo_story_highlight"),
        "geo_gourmet": matched.get("geo_gourmet"),
        "detour_suggestion": matched.get("detour_suggestion"),
        "photo_tip": matched.get("photo_tip"),
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
