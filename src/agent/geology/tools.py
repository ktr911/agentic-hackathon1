"""Tools used by the geology research agent."""


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
