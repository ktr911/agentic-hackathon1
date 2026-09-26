"""Aggregate Agent Runtime sessions into the admin dashboard summary."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

# Vertex AI list prices in USD (checked 2026-09). gemini-3.7-flash is on
# introductory pricing until 2026-12-31; thinking tokens bill as output.
TOKEN_PRICES_PER_MILLION = {
    "gemini-3.7-flash": (0.75, 3.75),
}
DEFAULT_TOKEN_PRICES = TOKEN_PRICES_PER_MILLION["gemini-3.7-flash"]
# gemini-3.1-flash-image, one 1K output image.
IMAGE_PRICE_USD = 0.067
# A turn without a final answer is still "running" until this much idle time.
RUNNING_GRACE = timedelta(minutes=10)
ROOT_AGENT = "root_agent"
# app.js appends client context (time, location) after this marker.
CLIENT_CONTEXT_MARKER = "[クライアントコンテキスト]"


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _parts(event: dict[str, Any]) -> list[dict[str, Any]]:
    return (event.get("content") or {}).get("parts") or []


def _usage_cost(raw: dict[str, Any]) -> tuple[int, int, float]:
    usage = raw.get("usageMetadata") or {}
    input_tokens = usage.get("promptTokenCount", 0)
    output_tokens = usage.get("candidatesTokenCount", 0) + usage.get(
        "thoughtsTokenCount", 0
    )
    input_price, output_price = TOKEN_PRICES_PER_MILLION.get(
        raw.get("modelVersion", ""), DEFAULT_TOKEN_PRICES
    )
    cost = (input_tokens * input_price + output_tokens * output_price) / 1_000_000
    return input_tokens, output_tokens, cost


def _tool_error(response: Any) -> str | None:
    if not isinstance(response, dict):
        return None
    if response.get("status") == "error" or "error" in response:
        return str(response.get("message") or response.get("error") or "error")
    return None


def _is_final_answer(event: dict[str, Any]) -> bool:
    if event.get("author") != ROOT_AGENT:
        return False
    parts = _parts(event)
    return any(part.get("text") for part in parts) and not any(
        "functionCall" in part for part in parts
    )


def summarize_session(
    session: dict[str, Any], events: list[dict[str, Any]], now: datetime
) -> dict[str, Any]:
    """Summarize one session's cost, turns, tool calls and errors."""
    session_id = session["name"].rsplit("/", 1)[-1]
    events = sorted(events, key=lambda event: event["timestamp"])
    turns: dict[str, list[dict[str, Any]]] = defaultdict(list)
    input_tokens = output_tokens = tool_calls = tool_errors = images = 0
    cost = 0.0
    errors: list[dict[str, str]] = []
    first_question = ""

    for event in events:
        turns[event.get("invocationId", "")].append(event)
        raw = event.get("rawEvent") or {}
        event_input, event_output, event_cost = _usage_cost(raw)
        input_tokens += event_input
        output_tokens += event_output
        cost += event_cost
        if raw.get("errorCode") or raw.get("errorMessage"):
            errors.append(
                {
                    "time": event["timestamp"],
                    "session": session_id,
                    "source": event.get("author", ""),
                    "message": str(raw.get("errorMessage") or raw.get("errorCode")),
                }
            )
        for part in _parts(event):
            if event.get("author") == "user" and part.get("text") and not first_question:
                first_question = part["text"].split(CLIENT_CONTEXT_MARKER)[0].strip()
            response = part.get("functionResponse")
            if response is None:
                continue
            tool_calls += 1
            payload = response.get("response")
            message = _tool_error(payload)
            if message:
                tool_errors += 1
                errors.append(
                    {
                        "time": event["timestamp"],
                        "session": session_id,
                        "source": response.get("name", ""),
                        "message": message,
                    }
                )
            elif response.get("name") == "generate_image":
                images += 1

    turn_summaries = []
    for turn_events in turns.values():
        if turn_events[0].get("author") != "user":
            continue
        started = _parse_time(turn_events[0]["timestamp"])
        last = _parse_time(turn_events[-1]["timestamp"])
        if any(_is_final_answer(event) for event in turn_events):
            status = "done"
        elif now - last < RUNNING_GRACE:
            status = "running"
        else:
            status = "incomplete"
        turn_summaries.append(
            {"status": status, "seconds": (last - started).total_seconds()}
        )

    statuses = {turn["status"] for turn in turn_summaries}
    if "incomplete" in statuses:
        status = "incomplete"
    elif "running" in statuses:
        status = "running"
    else:
        status = "done"

    return {
        "id": session_id,
        "user_id": session.get("userId", ""),
        "created": session.get("createTime", ""),
        "updated": session.get("updateTime", ""),
        "question": first_question,
        "turns": turn_summaries,
        "status": status,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "llm_cost": cost,
        "images": images,
        "cost": cost + images * IMAGE_PRICE_USD,
        "tool_calls": tool_calls,
        "tool_errors": tool_errors,
        "errors": errors,
    }


def build_summary(
    sessions: list[tuple[dict[str, Any], list[dict[str, Any]]]],
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build the dashboard payload from (session, events) pairs."""
    now = now or datetime.now(timezone.utc)
    rows = [summarize_session(session, events, now) for session, events in sessions]
    rows.sort(key=lambda row: row["updated"], reverse=True)

    turns = [turn for row in rows for turn in row["turns"]]
    done_seconds = [turn["seconds"] for turn in turns if turn["status"] == "done"]
    errors = sorted(
        (error for row in rows for error in row["errors"]),
        key=lambda error: error["time"],
        reverse=True,
    )
    day_ago = now - timedelta(days=1)
    tool_calls = sum(row["tool_calls"] for row in rows)
    tool_errors = sum(row["tool_errors"] for row in rows)
    latest = rows[0] if rows else None

    return {
        "generated_at": now.isoformat(),
        "cost": {
            "total": sum(row["cost"] for row in rows),
            "llm": sum(row["llm_cost"] for row in rows),
            "images": sum(row["images"] for row in rows) * IMAGE_PRICE_USD,
        },
        "latest_session": (
            {
                "id": latest["id"],
                "cost": latest["cost"],
                "question": latest["question"],
            }
            if latest
            else None
        ),
        "sessions": {
            "total": len(rows),
            "last_24h": sum(
                1 for row in rows if row["created"] and _parse_time(row["created"]) >= day_ago
            ),
            "users": len({row["user_id"] for row in rows}),
        },
        "latency": {
            "average": sum(done_seconds) / len(done_seconds) if done_seconds else None,
            "max": max(done_seconds) if done_seconds else None,
            "turns": len(done_seconds),
        },
        "tools": {
            "calls": tool_calls,
            "errors": tool_errors,
            "rate": tool_errors / tool_calls if tool_calls else 0.0,
        },
        "turns": {
            "total": len(turns),
            "done": sum(1 for turn in turns if turn["status"] == "done"),
            "running": sum(1 for turn in turns if turn["status"] == "running"),
            "incomplete": sum(1 for turn in turns if turn["status"] == "incomplete"),
        },
        "images": sum(row["images"] for row in rows),
        "tokens": {
            "input": sum(row["input_tokens"] for row in rows),
            "output": sum(row["output_tokens"] for row in rows),
        },
        "session_rows": [
            {
                key: row[key]
                for key in ("id", "user_id", "created", "question", "status", "cost")
            }
            | {"turns": len(row["turns"])}
            for row in rows
        ],
        "errors": errors[:20],
    }
