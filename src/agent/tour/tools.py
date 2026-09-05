"""Tools used by the tourism research agent."""


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
