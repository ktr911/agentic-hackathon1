"""Tools used by the tourism research agent with geology-linked routing."""

from typing import Any


def _get_geo_preset_by_location(
    location: str,
    geology_context: str | None = None,
) -> dict[str, Any]:
    """地域名や地質コンテキストから、地質ストーリーとスポット生成用プリセットを返します。"""
    loc_lower = location.lower() if location else ""
    geo_lower = geology_context.lower() if geology_context else ""

    # 箱根・火山カルデラ系
    if any(k in loc_lower for k in ["箱根", "hakone"]) or "カルデラ" in geo_lower or "地熱" in geo_lower:
        return {
            "region_theme": "箱根火山・カルデラ地形",
            "base_geo_story": "外輪山に囲まれたカルデラ地形と、断層運動・火山灰・地熱が織りなす大地の躍動。",
            "routes": {
                "A": {
                    "title": "【ルートA】カルデラ外輪山と断層パノラマ絶景コース",
                    "subtitle": "大地の隆起と火山の迫力を体感するアクティブ散策（所要約3.5時間・中級）",
                    "geo_focus": "外輪山の断層崖とカルデラ湖（芦ノ湖）のパノラマ展望、溶岩・火山灰露頭の観察",
                    "duration": "約3時間30分",
                    "difficulty": "中級（適度な起伏・展望トレッキング）",
                    "transportation": "徒歩＋周遊バス",
                    "next_prompt": "ルートAの詳細なタイムラインと持ち物を教えて",
                    "spots": [
                        {
                            "name": "カルデラ外輪山パノラマ展望台",
                            "category": "view",
                            "geo_point": "巨大噴火で陥没したカルデラと芦ノ湖、富士山を一望できる雄大な眺望点",
                            "highlight": "大地のスケールを実感する360度パノラマと記念撮影",
                            "stay_minutes": 45,
                            "offset": (0.005, 0.004),
                        },
                        {
                            "name": "火山性溶岩露頭・地層ウォーキング小道",
                            "category": "nature",
                            "geo_point": "幾重にも重なる火山灰層や溶岩流の跡が剥き出しになった迫力の露頭",
                            "highlight": "地層の縞模様を間近に観察しながらのネイチャーウォーク",
                            "stay_minutes": 40,
                            "offset": (0.001, 0.002),
                        },
                        {
                            "name": "絶景見晴らしテラスカフェ",
                            "category": "food",
                            "geo_point": "外輪山の稜線に佇み、地形のグラデーションを眺める休憩処",
                            "highlight": "絶景を眺めながらの特製ランチ＆焙煎珈琲",
                            "stay_minutes": 50,
                            "offset": (-0.003, 0.003),
                        },
                    ],
                },
                "B": {
                    "title": "【ルートB】大地の熱と清流をたどる癒やしの温泉・名水コース",
                    "subtitle": "地熱文化と火山灰層が磨いた清冽な湧水を巡るリラックス周遊（所要約2.5時間・初級）",
                    "geo_focus": "地下深くのマグマ熱が育む温泉・地熱蒸気、多孔質な火山礫層が濾過した清らかな伏流水",
                    "duration": "約2時間30分",
                    "difficulty": "初級（平坦な散策路と足湯でゆったり）",
                    "transportation": "徒歩",
                    "next_prompt": "ルートBの癒やしスポットや温泉・カフェを詳しく教えて",
                    "spots": [
                        {
                            "name": "地熱噴気・湯の花親水スポット",
                            "category": "nature",
                            "geo_point": "大地の熱エネルギーが立ち上る噴気孔と、ミネラル豊富な温泉の恵み",
                            "highlight": "温かい蒸気と温泉足湯でのんびりリフレッシュ",
                            "stay_minutes": 40,
                            "offset": (-0.002, -0.003),
                        },
                        {
                            "name": "湧水仕込み・古民家地熱甘味処",
                            "category": "food",
                            "geo_point": "火山岩層を通った軟水と地熱蒸気で作る名物蒸し菓子・和スイーツ",
                            "highlight": "温泉蒸し饅頭と名水点てのお抹茶",
                            "stay_minutes": 45,
                            "offset": (-0.004, 0.001),
                        },
                        {
                            "name": "深緑の湖畔せせらぎ小道",
                            "category": "view",
                            "geo_point": "火山堆積地特有の豊かな保水力に育まれたブナ・ヒノキの原生林",
                            "highlight": "マイナスイオンあふれる木漏れ日の湖畔ウォーキング",
                            "stay_minutes": 40,
                            "offset": (0.002, -0.002),
                        },
                    ],
                },
                "C": {
                    "title": "【ルートC】地形を活かした関所と旧街道ジオヒストリーコース",
                    "subtitle": "険しい外輪山を越える石畳街道と関所の歴史ロマン（所要約3時間・初〜中級）",
                    "geo_focus": "天然の要害となった外輪山のカルデラ壁と、火山岩（安山岩）の石畳が支えた東海道",
                    "duration": "約3時間",
                    "difficulty": "初〜中級（杉並木の歴史石畳歩道）",
                    "transportation": "徒歩",
                    "next_prompt": "ルートCの歴史街道と石畳の見どころを詳しく教えて",
                    "spots": [
                        {
                            "name": "旧東海道・安山岩の石畳杉並木",
                            "category": "culture",
                            "geo_point": "険しいカルデラ斜面を旅人が歩けるよう敷き詰めた地元の火山岩石畳",
                            "highlight": "樹齢数百年の杉並木と苔むす歴史石畳の静寂",
                            "stay_minutes": 50,
                            "offset": (0.003, -0.001),
                        },
                        {
                            "name": "要害の関所・ジオヒストリー館",
                            "category": "culture",
                            "geo_point": "山と湖に挟まれた極小の地形的ボトルネックに設置された天然の関所",
                            "highlight": "地形模型と古文書で紐解く交通要衝の歴史展示",
                            "stay_minutes": 40,
                            "offset": (-0.001, -0.004),
                        },
                        {
                            "name": "峠の茶屋・伝統力餅本舗",
                            "category": "food",
                            "geo_point": "険しい峠越えの旅人を支えてきた歴史ある峠の茶屋の佇まい",
                            "highlight": "つきたての名物力餅と香ばしい焙じ茶",
                            "stay_minutes": 40,
                            "offset": (-0.005, -0.002),
                        },
                    ],
                },
            },
        }

    # 鎌倉・海岸隆起・切通し系
    if any(k in loc_lower for k in ["鎌倉", "kamakura", "湘南"]) or "切通" in geo_lower or "砂岩" in geo_lower:
        return {
            "region_theme": "鎌倉・三浦層群と海成段丘・谷戸地形",
            "base_geo_story": "三方を囲む凝灰質砂岩の山と海が造り出した天然の要害。大地の固さを活かした切通しと海風の恵み。",
            "routes": {
                "A": {
                    "title": "【ルートA】谷戸の稜線と相模湾パノラマトレイルコース",
                    "subtitle": "隆起海岸段丘から海と古都を一望する絶景ハイキング（所要約3時間・中級）",
                    "geo_focus": "相模湾プレート運動による隆起段丘と侵食が生んだ急峻な尾根道・海への眺望",
                    "duration": "約3時間",
                    "difficulty": "中級（尾根歩き・階段あり）",
                    "transportation": "徒歩",
                    "next_prompt": "ルートAの絶景パノラマトレイルを詳しく教えて",
                    "spots": [
                        {
                            "name": "段丘スカイライン展望台",
                            "category": "view",
                            "geo_point": "古都の街並みと相模湾、遠く富士山まで見通す隆起段丘上の特等席",
                            "highlight": "海風を感じながらの雄大な水平線パノラマ",
                            "stay_minutes": 40,
                            "offset": (0.004, 0.003),
                        },
                        {
                            "name": "三浦層群の砂岩露頭トレイル",
                            "category": "nature",
                            "geo_point": "太古の海底堆積物が隆起した凝灰質砂泥岩の美しい縞模様地層",
                            "highlight": "化石や地層の観察ができる自然遊歩道散策",
                            "stay_minutes": 45,
                            "offset": (0.002, -0.002),
                        },
                        {
                            "name": "尾根の古民家オーガニックカフェ",
                            "category": "food",
                            "geo_point": "谷戸の緑に囲まれ、海風が通り抜ける心地よい高台の憩い場",
                            "highlight": "地元鎌倉野菜のプレートランチと自家製ハーブソーダ",
                            "stay_minutes": 50,
                            "offset": (-0.002, 0.002),
                        },
                    ],
                },
                "B": {
                    "title": "【ルートB】湧水と緑陰の谷戸（やと）カフェ散策コース",
                    "subtitle": "砂岩とローム層が育む豊かな地下水と隠れ家カフェを巡る（所要約2.5時間・初級）",
                    "geo_focus": "雨水を蓄えて染み出す砂岩層と、谷戸の底に集まる清冽な湧水・豊かな植生",
                    "duration": "約2時間30分",
                    "difficulty": "初級（木陰の平坦な小道が中心）",
                    "transportation": "徒歩",
                    "next_prompt": "ルートBの湧水カフェと谷戸散策のプランを詳しく教えて",
                    "spots": [
                        {
                            "name": "谷戸の清冽湧水庭園",
                            "category": "nature",
                            "geo_point": "砂岩の隙間から一年中途切れず湧き出す天然の伏流水と苔庭",
                            "highlight": "静寂に包まれた湧水池と青もみじ・苔の鑑賞",
                            "stay_minutes": 40,
                            "offset": (-0.001, 0.003),
                        },
                        {
                            "name": "名水仕込み・中庭テラス茶房",
                            "category": "food",
                            "geo_point": "湧水で丁寧に点てたお茶と、地元の季節菓子を提供する古民家処",
                            "highlight": "湧水仕込みの抹茶パフェと煎茶セット",
                            "stay_minutes": 50,
                            "offset": (-0.003, -0.001),
                        },
                        {
                            "name": "緑の竹林とやぐら（中世横穴墓）小径",
                            "category": "culture",
                            "geo_point": "柔らかい凝灰岩の岩壁を削って作られた中世特有の横穴遺構",
                            "highlight": "竹林のざわめきと岩肌に刻まれた歴史の気配",
                            "stay_minutes": 40,
                            "offset": (0.001, -0.004),
                        },
                    ],
                },
                "C": {
                    "title": "【ルートC】天然の要害・切通しと石切遺産ジオウォーク",
                    "subtitle": "岩盤を削り拓いた武士の要衝と石工の足跡をたどる（所要約3時間・初〜中級）",
                    "geo_focus": "外敵を防ぐため凝灰質砂岩の岩盤をV字に削り抜いた切通しの地質断面",
                    "duration": "約3時間",
                    "difficulty": "初〜中級（昔ながらの岩肌・土の道）",
                    "transportation": "徒歩",
                    "next_prompt": "ルートCの切通しや歴史スポットを詳しく教えて",
                    "spots": [
                        {
                            "name": "歴史の切通し・岩壁地層ロード",
                            "category": "culture",
                            "geo_point": "両脇にそびえる岩壁に刻まれたノミの跡と、地層の重なりが見事な古道",
                            "highlight": "かつての武士たちが駆け抜けた切通しの重厚な雰囲気",
                            "stay_minutes": 45,
                            "offset": (0.003, -0.003),
                        },
                        {
                            "name": "鎌倉石の石切場跡・工芸ギャラリー",
                            "category": "culture",
                            "geo_point": "寺社仏閣の石垣や参道に使われた地元産凝灰岩（鎌倉石）の採掘跡",
                            "highlight": "巨大な石切り壁の威容と現代職人の手仕事作品",
                            "stay_minutes": 40,
                            "offset": (-0.004, -0.002),
                        },
                        {
                            "name": "門前歴史甘味・瓦煎餅本舗",
                            "category": "food",
                            "geo_point": "門前町で古くから親しまれてきた銘菓と休息の場",
                            "highlight": "名物瓦煎餅と季節の葛きり",
                            "stay_minutes": 35,
                            "offset": (-0.002, 0.004),
                        },
                    ],
                },
            },
        }

    # 標準・デフォルト（丘陵・段丘・火山性堆積物・砂礫層）
    target_name = location if location and location != "指定なし" else "周辺エリア"
    return {
        "region_theme": f"{target_name}の台地・段丘と大地の恵み",
        "base_geo_story": "丘陵地の火山灰性ローム層と砂礫層が織りなす地形。豊かな地下水と見晴らしの良い段丘地形が地域の暮らしを支えています。",
        "routes": {
            "A": {
                "title": "【ルートA】大地を見渡すパノラマ段丘と地層観察コース",
                "subtitle": "高台のパノラマ眺望と剥き出しの地層露頭を巡るアクティブ散策（所要約3時間・中級）",
                "geo_focus": "台地と谷の高低差が生むパノラマ景観、砂礫層とローム層の境界露頭観察",
                "duration": "約3時間",
                "difficulty": "中級（段丘斜面の階段・アップダウンあり）",
                "transportation": "徒歩",
                "next_prompt": "ルートAの詳細なタイムテーブルと見どころを教えて",
                "spots": [
                    {
                        "name": "段丘トップ・みはらしパノラマ展望台",
                        "category": "view",
                        "geo_point": "段丘面の頂上から周辺の地形の起伏や遠くの山並みを一望できる展望地",
                        "highlight": "大地が刻んだ谷と尾根のパノラマ景観と写真撮影",
                        "stay_minutes": 40,
                        "offset": (0.004, 0.003),
                    },
                    {
                        "name": "砂礫層・ローム層の地層露頭観察ポイント",
                        "category": "nature",
                        "geo_point": "水を通しやすい砂礫層と赤土（ローム）が重なる大地の断面が露出した場所",
                        "highlight": "地層の手触りや大地の歴史を学べる露頭ウォーク",
                        "stay_minutes": 35,
                        "offset": (0.001, 0.002),
                    },
                    {
                        "name": "丘の上の展望カフェテラス",
                        "category": "food",
                        "geo_point": "段丘崖の縁に位置し、見下ろす街並みと風を感じる絶好のロケーション",
                        "highlight": "地元食材を使った焼き立てパンとオリジナルブレンド珈琲",
                        "stay_minutes": 45,
                        "offset": (-0.002, 0.004),
                    },
                ],
            },
            "B": {
                "title": "【ルートB】大地のフィルターが生む名水と段丘庭園コース",
                "subtitle": "清らかな湧水と段丘の緑に癒やされるのんびり散策（所要約2.5時間・初級）",
                "geo_focus": "砂礫層が天然の濾過装置となって湧き出す清冽な伏流水、水辺が育む植物群",
                "duration": "約2時間30分",
                "difficulty": "初級（段丘下の平坦な親水緑道）",
                "transportation": "徒歩",
                "next_prompt": "ルートBの湧水スポットやカフェの詳しいプランを教えて",
                "spots": [
                    {
                        "name": "段丘崖下の清冽な湧水親水池",
                        "category": "nature",
                        "geo_point": "不透水層の境目からこんこんと湧き出す透明度抜群の清流池",
                        "highlight": "澄んだ湧水に泳ぐ水草や小魚を眺めてクールダウン",
                        "stay_minutes": 40,
                        "offset": (-0.001, 0.003),
                    },
                    {
                        "name": "名水仕込み・湧水庵カフェ＆郷土膳",
                        "category": "food",
                        "geo_point": "大地の恵みである湧水で打った自慢の麺や名水珈琲を味わえる古民家処",
                        "highlight": "名水仕込みのランチ御膳と季節の甘味",
                        "stay_minutes": 50,
                        "offset": (-0.003, 0.001),
                    },
                    {
                        "name": "水路と段丘のせせらぎ里山小径",
                        "category": "culture",
                        "geo_point": "湧水を農業や生活に利用してきた人々の工夫が残る親水散策路",
                        "highlight": "せせらぎの音を聞きながら四季折々の草花を楽しむ散策",
                        "stay_minutes": 40,
                        "offset": (-0.004, -0.003),
                    },
                ],
            },
            "C": {
                "title": "【ルートC】地形を活かした古道と郷土のジオヒストリーコース",
                "subtitle": "人が大地とともに歩んできた歴史遺産と石造文化をたどる（所要約3時間・初〜中級）",
                "geo_focus": "氾濫を避けて段丘上に拓かれた古道、地元の石材を活用した石仏・石垣遺構",
                "duration": "約3時間",
                "difficulty": "初〜中級（舗装された歴史道・神社参道）",
                "transportation": "徒歩",
                "next_prompt": "ルートCの歴史古道と石造文化の見どころを詳しく教えて",
                "spots": [
                    {
                        "name": "段丘尾根の歴史古道・街道並木",
                        "category": "culture",
                        "geo_point": "水害を避けて段丘の一番高い尾根筋に作られた古くからの主要街道",
                        "highlight": "古い道標や庚申塔が点在するノスタルジックな古道歩き",
                        "stay_minutes": 45,
                        "offset": (0.003, -0.002),
                    },
                    {
                        "name": "地元石材の石造遺産・郷土文化館",
                        "category": "culture",
                        "geo_point": "地域の地層から切り出された石を使った石垣や建築の歴史展示",
                        "highlight": "大地と人々の営みの結びつきを体感する企画展示",
                        "stay_minutes": 40,
                        "offset": (-0.002, -0.004),
                    },
                    {
                        "name": "門前茶屋・地場甘味処",
                        "category": "food",
                        "geo_point": "古道沿いで昔から旅人に愛されてきた名物餅と煎茶の休憩処",
                        "highlight": "香ばしい焼き団子とお抹茶でほっと一服",
                        "stay_minutes": 35,
                        "offset": (-0.005, -0.001),
                    },
                ],
            },
        },
    }


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
    loc_str = location if location and location.strip() else "指定エリア"

    preset = _get_geo_preset_by_location(loc_str, geology_context)
    routes_data = preset["routes"]

    route_options = []
    all_map_points = []

    for route_id, r in routes_data.items():
        # ルートごとのスポットとピン
        route_spots = []
        for s_idx, spot in enumerate(r["spots"]):
            order = s_idx + 1
            lat_off, lng_off = spot["offset"]
            s_lat = round(center_lat + lat_off, 5)
            s_lng = round(center_lng + lng_off, 5)

            spot_detail = {
                "order": order,
                "name": spot["name"],
                "category": spot["category"],
                "geo_point": spot["geo_point"],
                "highlight": spot["highlight"],
                "stay_minutes": spot["stay_minutes"],
                "latitude": s_lat,
                "longitude": s_lng,
            }
            route_spots.append(spot_detail)

            # 代表ピン（各ルートからピックアップ、またはルートAメイン）
            if route_id == "A" or s_idx == 0:
                all_map_points.append({
                    "title": f"[{route_id}-{order}] {spot['name']}",
                    "latitude": s_lat,
                    "longitude": s_lng,
                    "category": spot["category"],
                })

        route_options.append({
            "route_id": route_id,
            "title": r["title"],
            "subtitle": r["subtitle"],
            "geo_focus": r["geo_focus"],
            "duration": r["duration"],
            "difficulty": r["difficulty"],
            "transportation": r["transportation"],
            "spots": route_spots,
            "next_prompt_suggestion": r["next_prompt"],
        })

    return {
        "is_mock": True,
        "location": loc_str,
        "region_theme": preset["region_theme"],
        "base_geo_story": preset["base_geo_story"],
        "route_options": route_options,
        "map_points": all_map_points,
        "selection_guide": (
            "お好みのルートをお選びいただけます。「ルートAを詳しく教えて」「ルートBのタイムラインを見せて」"
            "「ルートCの歴史スポットを変更したい」などとお伝えいただければ、具体的な行程や見どころをご案内します。"
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
    """特定のルート（ルートA/B/C）について詳細なタイムライン・地質解説・行き先を策定します。

    Args:
        location: 調査対象の地域名。
        latitude: 中心地点または現在地の緯度。
        longitude: 中心地点または現在地の経度。
        theme: 観光のテーマ。
        duration_hours: 想定する観光所要時間。
        transportation: 主な移動手段。
        geology_context: 地質特徴の要約。
        selected_route_id: 選択されたルートID（"A", "B", "C"）。指定がなければ"A"。
    """
    center_lat = latitude if latitude is not None else 35.0116
    center_lng = longitude if longitude is not None else 135.7681
    loc_str = location if location and location.strip() else "指定地域"
    route_key = selected_route_id.upper() if selected_route_id and selected_route_id.upper() in ["A", "B", "C"] else "A"

    preset = _get_geo_preset_by_location(loc_str, geology_context)
    selected_route = preset["routes"].get(route_key, preset["routes"]["A"])

    destinations = []
    map_points = []
    itinerary = []

    # タイムライン構築（10:00開始を想定）
    current_hour = 10
    current_minute = 0
    transport = transportation if transportation else selected_route["transportation"]

    for idx, spot in enumerate(selected_route["spots"]):
        order = idx + 1
        lat_offset, lng_offset = spot["offset"]
        spot_lat = round(center_lat + lat_offset, 5)
        spot_lng = round(center_lng + lng_offset, 5)
        stay_mins = int(spot["stay_minutes"])

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
            "name": spot["name"],
            "category": spot["category"],
            "geo_point": spot["geo_point"],
            "highlight": spot["highlight"],
            "stay_minutes": stay_mins,
            "latitude": spot_lat,
            "longitude": spot_lng,
        }
        destinations.append(dest_info)

        is_last = idx == len(selected_route["spots"]) - 1
        next_transit = (
            "最寄り駅・交通拠点へ移動しゴール"
            if is_last
            else f"{transport}で約10〜15分移動"
        )

        itinerary.append({
            "step": order,
            "time_window": f"{arrival_time} - {departure_time}",
            "spot_name": spot["name"],
            "geo_story": spot["geo_point"],
            "activity": f"{spot['highlight']}（地質見どころ: {spot['geo_point']}）",
            "next_transit": next_transit,
        })

        map_points.append({
            "title": f"[{order}] {spot['name']}",
            "latitude": spot_lat,
            "longitude": spot_lng,
            "category": spot["category"],
        })

    travel_advice = [
        f"移動手段: {transport}（コース難易度: {selected_route['difficulty']}）。",
        "地質の露頭や展望台周辺は岩肌・階段・未舗装路があるため、歩きやすい靴でお越しください。",
        f"次のアクション提案: 「このルートのカフェを変更」「所要時間を短くしたい」「雨天時の代替プラン」など柔軟にカスタマイズできます。",
    ]

    return {
        "is_mock": True,
        "location": loc_str,
        "selected_route_id": route_key,
        "route_title": selected_route["title"],
        "subtitle": selected_route["subtitle"],
        "geo_focus": selected_route["geo_focus"],
        "summary": f"{preset['base_geo_story']} {selected_route['subtitle']}",
        "total_duration": selected_route["duration"],
        "difficulty": selected_route["difficulty"],
        "transportation": transport,
        "destinations": destinations,
        "itinerary": itinerary,
        "travel_advice": travel_advice,
        "map_points": map_points,
        # 互換プロパティ
        "recommended_spots": [d["name"] for d in destinations],
        "sample_plan": " -> ".join([d["name"] for d in destinations]),
    }


def get_mock_tourism_report(
    location: str,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict[str, Any]:
    """後方互換用：地質サジェストを含めたモック観光調査・ルートレポートを返します。"""
    multi = suggest_geo_tour_routes(location, None, latitude, longitude)
    single = plan_tour_route(location, latitude, longitude, selected_route_id="A")

    return {
        **single,
        "route_options": multi["route_options"],
        "region_theme": multi["region_theme"],
        "base_geo_story": multi["base_geo_story"],
        "selection_guide": multi["selection_guide"],
    }
