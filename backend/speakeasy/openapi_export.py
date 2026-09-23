"""Generate and verify the committed OpenAPI schema.

The schema starts from the FastAPI app and is extended with the WebSocket
event models, so the GUI can generate its TypeScript types from one file.
"""

import copy
import json
from pathlib import Path

from .contracts import WS_EVENT_MODELS
from .server import app

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "openapi.json"


def build_schema() -> dict:
    """Return the FastAPI schema merged with the WebSocket event components."""
    schema = copy.deepcopy(app.openapi())
    schemas = schema.setdefault("components", {}).setdefault("schemas", {})

    for name, model in WS_EVENT_MODELS.items():
        model_schema = model.model_json_schema(ref_template="#/components/schemas/{model}")
        for def_name, def_schema in model_schema.pop("$defs", {}).items():
            schemas[def_name] = def_schema
        schemas[name] = model_schema

    return schema


def render() -> str:
    """Serialize the schema exactly as it is committed."""
    return json.dumps(build_schema(), indent=2, sort_keys=True) + "\n"


def write() -> Path:
    """Write the schema to backend/openapi.json and return its path."""
    SCHEMA_PATH.write_text(render(), encoding="utf-8", newline="\n")
    return SCHEMA_PATH


def check() -> bool:
    """Return True when the committed file already matches the schema."""
    committed = SCHEMA_PATH.read_bytes().decode("utf-8") if SCHEMA_PATH.exists() else ""
    if committed == render():
        return True

    print(f"{SCHEMA_PATH} is out of date.")
    print("Run: uv run python scripts/export_openapi.py")
    return False
