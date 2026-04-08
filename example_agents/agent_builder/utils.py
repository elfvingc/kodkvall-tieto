import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal


MODEL = os.environ.get("MISTRAL_MODEL", "mistral-small-latest")
ARTIFACTS_ROOT = Path(__file__).resolve().parent / "artifacts"
DEFAULT_TASK = os.environ.get(
    "MISTRAL_DEFAULT_TASK",
    "Build an agent that helps sales reps prepare for customer meetings",
)


def create_client():
    try:
        from mistralai import Mistral  # type: ignore[import-not-found]
    except ImportError:
        raise RuntimeError(
            "Could not import Mistral with 'from mistralai import Mistral'. Install the matching SDK version from requirements.txt."
        )

    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError("Missing MISTRAL_API_KEY environment variable.")
    return Mistral(api_key=api_key)


def call_mistral(
    messages,
    tools=None,
    tool_choice: Literal["auto", "none", "any", "required"] = "none",
    parallel_tool_calls=False,
):
    client = create_client()
    return client.chat.complete(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice=tool_choice,
        parallel_tool_calls=parallel_tool_calls,
    )


def extract_json_payload(content):
    if isinstance(content, str):
        text = content.strip()
    elif isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text_part = item.get("text")
            else:
                text_part = getattr(item, "text", None)
            if text_part:
                parts.append(text_part)
        text = "\n".join(parts).strip()
    else:
        text = str(content).strip()

    candidates = []
    candidates.extend(re.findall(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE))

    for start_char, end_char in (("{", "}"), ("[", "]")):
        start_index = text.find(start_char)
        end_index = text.rfind(end_char)
        if start_index != -1 and end_index != -1 and end_index > start_index:
            candidates.append(text[start_index:end_index + 1])

    candidates.append(text)

    seen = set()
    for candidate in candidates:
        normalized = candidate.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        try:
            return json.loads(normalized)
        except json.JSONDecodeError:
            continue

    raise ValueError(f"Could not parse JSON from model response: {text[:500]}")


def extract_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text_part = item.get("text")
            else:
                text_part = getattr(item, "text", None)
            if text_part:
                parts.append(text_part)
        return "\n".join(parts)
    return str(content)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "agent-run"


def ensure_artifact_dir(run_id: str | None = None) -> Path:
    if run_id is None:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        run_id = f"run-{timestamp}"
    artifact_dir = ARTIFACTS_ROOT / run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    return artifact_dir


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def print_step(name: str) -> None:
    print(f"\n== {name} ==")


def save_pipeline_artifacts(artifact_dir: Path, name: str, payload: Any) -> Path:
    path = artifact_dir / name
    write_json(path, payload)
    return path


def load_required_json(artifact_dir: Path, filename: str) -> dict[str, Any]:
    path = artifact_dir / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing required artifact: {path}")
    return read_json(path)
