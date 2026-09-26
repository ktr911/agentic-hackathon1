"""Cloud Run web server and authenticated Agent Runtime proxy."""

from __future__ import annotations

import asyncio
import base64
import hmac
import os
import time
import re
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import google.auth
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.cloud import storage

from admin import build_summary

STATIC_DIR = Path(__file__).parent
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "asia-northeast1")
AGENT_ENGINE_RESOURCE = os.getenv("AGENT_ENGINE_RESOURCE", "")
ARTIFACT_BUCKET = os.getenv("ARTIFACT_BUCKET", "")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
ADMIN_SESSION_LIMIT = 200
ADMIN_CACHE_SECONDS = 30
_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._~-]{0,255}$")

app = FastAPI(title="Fieldnote Agent web", docs_url=None, redoc_url=None)

_credentials = None
_credentials_lock = asyncio.Lock()


def _require_configuration() -> None:
    missing = [
        name
        for name, value in (
            ("GOOGLE_CLOUD_PROJECT", PROJECT_ID),
            ("AGENT_ENGINE_RESOURCE", AGENT_ENGINE_RESOURCE),
        )
        if not value
    ]
    if missing:
        raise HTTPException(
            status_code=503,
            detail=f"Server configuration is incomplete: {', '.join(missing)}",
        )


async def _access_token() -> str:
    """Return a cached ADC access token, refreshing it outside the event loop."""
    global _credentials
    async with _credentials_lock:
        if _credentials is None:
            _credentials, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
        expiry = getattr(_credentials, "expiry", None)
        if expiry is None:
            expires_soon = True
        else:
            now = datetime.now(expiry.tzinfo or timezone.utc)
            if expiry.tzinfo is None:
                now = now.replace(tzinfo=None)
            expires_soon = (expiry - now).total_seconds() < 60
        if not _credentials.valid or expires_soon:
            await asyncio.to_thread(_credentials.refresh, GoogleAuthRequest())
        return _credentials.token


def _agent_endpoint(method: str) -> str:
    return (
        f"https://{LOCATION}-aiplatform.googleapis.com/v1/"
        f"{AGENT_ENGINE_RESOURCE}:{method}"
    )


def _unwrap_output(payload: Any) -> Any:
    if isinstance(payload, dict) and "output" in payload:
        return payload["output"]
    return payload


async def _query_agent(class_method: str, method_input: dict[str, Any]) -> Any:
    _require_configuration()
    token = await _access_token()
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            _agent_endpoint("query"),
            headers={"Authorization": f"Bearer {token}"},
            json={"class_method": class_method, "input": method_input},
        )
    if response.is_error:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return _unwrap_output(response.json())


@app.get("/healthz")
@app.get("/api/healthz")
async def healthz() -> dict[str, Any]:
    return {
        "status": "ok",
        "configured": bool(PROJECT_ID and AGENT_ENGINE_RESOURCE),
    }


@app.get("/list-apps")
async def list_apps() -> list[str]:
    _require_configuration()
    return ["agent"]


@app.post("/apps/{app_name}/users/{user_id}/sessions")
async def create_session(app_name: str, user_id: str) -> Any:
    if app_name != "agent":
        raise HTTPException(status_code=404, detail="Unknown app")
    return await _query_agent("async_create_session", {"user_id": user_id})


async def _close_stream(
    response: httpx.Response, client: httpx.AsyncClient
) -> AsyncIterator[bytes]:
    """Re-frame Agent Runtime's newline-delimited JSON as SSE for the client."""
    try:
        async for line in response.aiter_lines():
            line = line.strip()
            if not line:
                continue
            if not line.startswith("data:"):
                line = f"data: {line}"
            yield f"{line}\n\n".encode()
    finally:
        await response.aclose()
        await client.aclose()


@app.post("/run_sse")
async def run_sse(request: Request) -> StreamingResponse:
    _require_configuration()
    body = await request.json()
    try:
        user_id = body["userId"]
        session_id = body["sessionId"]
        parts = body["newMessage"]["parts"]
        message = "\n".join(part["text"] for part in parts if part.get("text"))
    except (KeyError, TypeError) as error:
        raise HTTPException(
            status_code=400, detail="Invalid ADK request body"
        ) from error
    if not message:
        raise HTTPException(status_code=400, detail="Message is empty")

    token = await _access_token()
    client = httpx.AsyncClient(timeout=httpx.Timeout(900, connect=15))
    upstream_request = client.build_request(
        "POST",
        f"{_agent_endpoint('streamQuery')}?alt=sse",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "text/event-stream",
        },
        json={
            "class_method": "async_stream_query",
            "input": {
                "user_id": user_id,
                "session_id": session_id,
                "message": message,
            },
        },
    )
    upstream = await client.send(upstream_request, stream=True)
    if upstream.is_error:
        error_body = (await upstream.aread()).decode(errors="replace")
        await upstream.aclose()
        await client.aclose()
        raise HTTPException(status_code=upstream.status_code, detail=error_body)

    return StreamingResponse(
        _close_stream(upstream, client),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _validate_segment(value: str, label: str) -> None:
    if not _SAFE_SEGMENT.fullmatch(value):
        raise HTTPException(status_code=400, detail=f"Invalid {label}")


@app.get(
    "/apps/{app_name}/users/{user_id}/sessions/{session_id}/artifacts/"
    "{filename}/versions/{version}"
)
async def get_artifact(
    app_name: str,
    user_id: str,
    session_id: str,
    filename: str,
    version: int,
) -> JSONResponse:
    if not ARTIFACT_BUCKET:
        raise HTTPException(status_code=503, detail="ARTIFACT_BUCKET is not set")
    for value, label in (
        (app_name, "app name"),
        (user_id, "user ID"),
        (session_id, "session ID"),
        (filename, "filename"),
    ):
        _validate_segment(value, label)
    if version < 0:
        raise HTTPException(status_code=400, detail="Invalid artifact version")

    bucket = storage.Client(project=PROJECT_ID).bucket(ARTIFACT_BUCKET)
    runtime_app_name = AGENT_ENGINE_RESOURCE.rsplit("/", 1)[-1]
    app_names = dict.fromkeys((app_name, runtime_app_name))
    blob = None
    for artifact_app_name in app_names:
        object_name = f"{artifact_app_name}/{user_id}/{session_id}/{filename}/{version}"
        blob = await asyncio.to_thread(bucket.get_blob, object_name)
        if blob is not None:
            break
    if blob is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    data = await asyncio.to_thread(blob.download_as_bytes)
    return JSONResponse(
        {
            "inlineData": {
                "mimeType": blob.content_type or "application/octet-stream",
                "data": base64.b64encode(data).decode("ascii"),
            }
        }
    )


def _require_admin(request: Request) -> None:
    if not ADMIN_TOKEN:
        raise HTTPException(status_code=503, detail="ADMIN_TOKEN is not set")
    supplied = request.headers.get("authorization", "").removeprefix("Bearer ")
    if not hmac.compare_digest(supplied.encode(), ADMIN_TOKEN.encode()):
        raise HTTPException(status_code=401, detail="Invalid admin token")


async def _list_all(
    client: httpx.AsyncClient, url: str, key: str, limit: int
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    params: dict[str, Any] = {"pageSize": 100}
    while len(items) < limit:
        response = await client.get(url, params=params)
        if response.is_error:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        payload = response.json()
        items.extend(payload.get(key, []))
        if not payload.get("nextPageToken"):
            break
        params["pageToken"] = payload["nextPageToken"]
    return items[:limit]


_admin_cache: tuple[float, dict[str, Any]] | None = None
_admin_lock = asyncio.Lock()


async def _collect_sessions() -> list[tuple[dict[str, Any], list[dict[str, Any]]]]:
    token = await _access_token()
    base = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1"
    semaphore = asyncio.Semaphore(8)
    async with httpx.AsyncClient(
        timeout=60, headers={"Authorization": f"Bearer {token}"}
    ) as client:
        sessions = await _list_all(
            client,
            f"{base}/{AGENT_ENGINE_RESOURCE}/sessions",
            "sessions",
            ADMIN_SESSION_LIMIT,
        )

        async def with_events(session: dict[str, Any]):
            async with semaphore:
                events = await _list_all(
                    client, f"{base}/{session['name']}/events", "sessionEvents", 2000
                )
            return session, events

        return await asyncio.gather(*(with_events(session) for session in sessions))


@app.get("/admin")
async def admin_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "admin.html")


@app.get("/api/admin/summary")
async def admin_summary(request: Request, refresh: bool = False) -> dict[str, Any]:
    _require_admin(request)
    _require_configuration()
    global _admin_cache
    async with _admin_lock:
        if (
            refresh
            or _admin_cache is None
            or time.monotonic() - _admin_cache[0] > ADMIN_CACHE_SECONDS
        ):
            _admin_cache = (time.monotonic(), build_summary(await _collect_sessions()))
        return _admin_cache[1]


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
