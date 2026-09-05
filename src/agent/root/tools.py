"""Tools used by the root orchestration agent."""

from uuid import uuid4

from google import genai
from google.adk.tools import ToolContext
from google.genai import types

from ..config import IMAGE_MODEL
from ..geology.tools import get_mock_geology_report
from ..tour.tools import get_mock_tourism_report


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
