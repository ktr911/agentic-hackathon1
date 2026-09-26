"""Tools used by the geology research agent."""

import asyncio
import json
import urllib.error
import urllib.request
from typing import Any

from google.adk.tools import ToolContext

GEOLOGY_API_URL = "https://gbank.gsj.jp/seamless/v2/api/1.2/legend.json"
GEOLOGY_API_SOURCE = "産業技術総合研究所 地質調査総合センター シームレス地質図V2"
REQUEST_TIMEOUT_SECONDS = 10

_DEFAULT_LATITUDE = 35.2324
_DEFAULT_LONGITUDE = 139.1069
# セッション state のキー。地質・観光・地図の各ツールで凡例を使い回す。
LEGEND_STATE_KEY = "geology_legend"


async def lookup_legend(
    latitude: float, longitude: float, state: Any
) -> dict[str, Any]:
    """地点の凡例を返します。同じ地点なら state のキャッシュを使います。

    戻り値は {"legend": {...}} か {"error": "..."} のどちらかです。
    """
    key = f"{latitude:.5f},{longitude:.5f}"
    cached = state.get(LEGEND_STATE_KEY)
    if isinstance(cached, dict) and cached.get("key") == key:
        return cached

    try:
        legend = await asyncio.to_thread(_fetch_legend, latitude, longitude)
    except _GeologyApiError as exc:
        return {"error": str(exc)}
    state[LEGEND_STATE_KEY] = {"key": key, "legend": legend}
    return {"legend": legend}


def describe_legend(legend: dict[str, Any]) -> str:
    """凡例を「岩相（地質区分）、形成年代」の一文にまとめます。"""
    return (
        f"{legend.get('lithology_ja', '不明')}（{legend.get('group_ja', '不明')}）、"
        f"形成年代: {legend.get('formationAge_ja', '不明')}"
    )


async def get_geology_report(
    location: str,
    tool_context: ToolContext,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict[str, object]:
    """指定地点の地質情報を、シームレス地質図V2 Web APIから取得します。

    Args:
        location: 調査対象の地域名。指定がなければ「指定なし」。
        tool_context: ADKが注入する現在のツール実行コンテキスト。
        latitude: クライアントから渡された中心地点の緯度。
        longitude: クライアントから渡された中心地点の経度。
    """
    center_latitude = latitude if latitude is not None else _DEFAULT_LATITUDE
    center_longitude = longitude if longitude is not None else _DEFAULT_LONGITUDE

    result = await lookup_legend(center_latitude, center_longitude, tool_context.state)
    legend = result.get("legend")
    if legend is None:
        return {
            "is_mock": False,
            "location": location,
            "latitude": center_latitude,
            "longitude": center_longitude,
            "source": GEOLOGY_API_SOURCE,
            "error": result["error"],
            "summary": (
                "地質情報を取得できませんでした"
                "（海域や地質図の整備範囲外の可能性があります）。"
            ),
            "findings": [],
            "map_points": [],
        }

    group_ja = legend.get("group_ja", "不明")
    lithology_ja = legend.get("lithology_ja", "不明")
    formation_age_ja = legend.get("formationAge_ja", "不明")

    return {
        "is_mock": False,
        "location": location,
        "latitude": center_latitude,
        "longitude": center_longitude,
        "source": GEOLOGY_API_SOURCE,
        "summary": f"{lithology_ja}（{group_ja}）が分布しています。形成年代は{formation_age_ja}です。",
        "findings": [
            f"地質区分: {group_ja}",
            f"岩相: {lithology_ja}",
            f"形成年代: {formation_age_ja}",
        ],
        "map_points": [
            {
                "title": f"{lithology_ja}（{group_ja}）",
                "latitude": center_latitude,
                "longitude": center_longitude,
                "category": "geology",
            },
        ],
    }


class _GeologyApiError(Exception):
    """地質図APIからの取得に失敗した場合の内部エラー。"""


def _fetch_legend(latitude: float, longitude: float) -> dict[str, object]:
    url = f"{GEOLOGY_API_URL}?point={latitude},{longitude}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "agentic-hackathon-geology-agent/1.0"},
    )

    try:
        with urllib.request.urlopen(
            request, timeout=REQUEST_TIMEOUT_SECONDS
        ) as response:
            body = response.read()
    except urllib.error.HTTPError as exc:
        raise _GeologyApiError(
            f"地質図APIがエラーを返しました（HTTP {exc.code}）。"
        ) from exc
    except urllib.error.URLError as exc:
        raise _GeologyApiError(
            f"地質図APIに接続できませんでした（{exc.reason}）。"
        ) from exc
    except TimeoutError as exc:
        raise _GeologyApiError("地質図APIへの接続がタイムアウトしました。") from exc

    if not body:
        raise _GeologyApiError("指定地点の地質情報が見つかりませんでした。")

    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise _GeologyApiError("地質図APIの応答を解析できませんでした。") from exc

    if isinstance(data, dict) and "code" in data and "symbol" not in data:
        message = data.get("message", {})
        detail = message.get("ja") if isinstance(message, dict) else None
        raise _GeologyApiError(detail or "地質図APIがエラーを返しました。")

    if not isinstance(data, dict):
        raise _GeologyApiError("地質図APIの応答形式が不正です。")

    return data


# 後方互換のためのエイリアス。他エージェントからの参照名を変えないために残す。
get_mock_geology_report = get_geology_report
