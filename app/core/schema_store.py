"""
app/core/schema_store.py

In-memory store for live schema + user-defined metadata.
Descriptions and table selections are persisted to disk as JSON
so they survive backend restarts and can be reloaded on next session.

Storage location: data/schema_configs/<db_type>_<db_name>.json

Internal _store structure:
{
    "tables": [
        {
            "table":       "orders",
            "row_count":   99441,
            "selected":    True,
            "description": "Core transaction table...",
            "columns": [
                {"name": "order_id", "type": "varchar(50)", "description": "Unique order ID"}
            ]
        },
        ...
    ],
    "db_type": "mysql",
    "db_name": "olist_db"
}
"""

import os
import json
from app.core.logging_config import setup_logger

logger = setup_logger(__name__)

CONFIGS_DIR = "data/schema_configs"

_store: dict = {
    "tables":  [],
    "db_type": None,
    "db_name": None,
}


# ── Disk helpers ──────────────────────────────────────────────────────────────

def _config_path(db_type: str, db_name: str) -> str:
    """Return the JSON file path for a given DB type + name."""
    os.makedirs(CONFIGS_DIR, exist_ok=True)
    safe_name = db_name.replace("/", "_").replace("\\", "_").replace(":", "_")
    return os.path.join(CONFIGS_DIR, f"{db_type}_{safe_name}.json")


def _save_to_disk():
    """
    Persist the entire _store to disk.
    Called automatically after every save_table_metadata() call.
    """
    if not _store.get("db_type") or not _store.get("db_name"):
        return
    path = _config_path(_store["db_type"], _store["db_name"])
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(_store, f, indent=2, ensure_ascii=False)
        logger.info(f"[SchemaStore] Saved to disk: {path}")
    except Exception as e:
        logger.error(f"[SchemaStore] Failed to save to disk: {e}")


def _load_from_disk(db_type: str, db_name: str) -> dict | None:
    """
    Load a previously saved config from disk.
    Returns the stored dict or None if no file exists.
    """
    path = _config_path(db_type, db_name)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"[SchemaStore] Loaded saved config from disk: {path}")
        return data
    except Exception as e:
        logger.error(f"[SchemaStore] Failed to load from disk: {e}")
        return None


def _merge_descriptions(live_tables: list, saved_tables: list) -> list:
    """
    Merge saved descriptions into freshly-read live schema.
    Live schema is always the source of truth for table/column structure.
    Saved data only provides: selected, description, column descriptions.
    This way if the DB schema changed (new columns added), we still pick them up.
    """
    saved_map = {t["table"]: t for t in saved_tables}
    merged = []
    for t in live_tables:
        tname   = t["table"]
        saved_t = saved_map.get(tname, {})
        merged_t = {
            "table":       tname,
            "row_count":   t["row_count"],
            "selected":    saved_t.get("selected", True),
            "description": saved_t.get("description", ""),
        }
        saved_col_map = {c["name"]: c for c in saved_t.get("columns", [])}
        merged_t["columns"] = [
            {
                "name":        c["name"],
                "type":        c["type"],
                "description": saved_col_map.get(c["name"], {}).get("description", "")
            }
            for c in t["columns"]
        ]
        merged.append(merged_t)
    return merged


# ── List all saved configs ────────────────────────────────────────────────────

def list_saved_configs() -> list[dict]:
    """
    Return a list of all saved schema configs from disk.
    Each entry: { db_type, db_name, table_count, selected_count, path, has_descriptions }
    Used by the Connect page to show "Saved Configurations" cards.
    """
    os.makedirs(CONFIGS_DIR, exist_ok=True)
    configs = []
    for fname in sorted(os.listdir(CONFIGS_DIR)):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(CONFIGS_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            tables          = data.get("tables", [])
            selected_count  = sum(1 for t in tables if t.get("selected", False))
            has_descriptions = any(
                t.get("description") or any(c.get("description") for c in t.get("columns", []))
                for t in tables
            )
            configs.append({
                "db_type":         data.get("db_type", "?"),
                "db_name":         data.get("db_name", "?"),
                "table_count":     len(tables),
                "selected_count":  selected_count,
                "has_descriptions": has_descriptions,
                "filename":        fname,
            })
        except Exception:
            continue
    return configs


def load_saved_config(filename: str) -> bool:
    """
    Load a specific saved config file directly into _store.
    Does NOT reconnect to DB — just restores schema + descriptions.
    Returns True on success.
    """
    global _store
    fpath = os.path.join(CONFIGS_DIR, filename)
    if not os.path.exists(fpath):
        logger.error(f"[SchemaStore] File not found: {fpath}")
        return False
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        _store = data
        logger.info(
            f"[SchemaStore] Loaded config '{filename}': "
            f"{len(_store['tables'])} tables, db={_store['db_name']}"
        )
        return True
    except Exception as e:
        logger.error(f"[SchemaStore] Failed to load config: {e}")
        return False


# ── Core lifecycle ────────────────────────────────────────────────────────────

def refresh_schema() -> dict:
    """
    Read raw schema from active DB, merge with any saved descriptions, cache in _store.
    Called by POST /connect immediately after connection succeeds.
    """
    global _store

    from app.core.database import get_active_config
    from app.core.connectors import get_schema

    config  = get_active_config()
    db_type = config.get("type", "mysql")
    db_name = config.get("database") or config.get("file", "?")

    logger.info(f"[SchemaStore] Reading schema from {db_type.upper()} / {db_name}")

    raw = get_schema(config)

    live_tables = [
        {
            "table":       t["table"],
            "row_count":   t.get("row_count", 0),
            "selected":    True,
            "description": "",
            "columns": [
                {"name": c["name"], "type": c["type"], "description": ""}
                for c in t.get("columns", [])
            ]
        }
        for t in raw
    ]

    # Auto-merge saved descriptions if this DB was configured before
    saved = _load_from_disk(db_type, db_name)
    if saved:
        logger.info(f"[SchemaStore] Found saved config for {db_name} — merging descriptions")
        live_tables = _merge_descriptions(live_tables, saved.get("tables", []))

    _store = {"tables": live_tables, "db_type": db_type, "db_name": db_name}
    logger.info(f"[SchemaStore] Store ready: {len(live_tables)} tables")
    return _store


def reset_schema():
    """
    Clear the live schema store and fall back to hardcoded schema_metadata.py.
    Called by POST /disconnect.
    """
    global _store
    _store = {"tables": [], "db_type": None, "db_name": None}
    logger.info("[SchemaStore] Schema cleared — agents fall back to Olist schema_metadata.py")


# ── Read helpers ──────────────────────────────────────────────────────────────

def is_live_schema_available() -> bool:
    return bool(_store.get("tables"))

def get_db_type() -> str | None:
    return _store.get("db_type")

def get_store() -> dict:
    return _store

def get_selected_tables() -> list[dict]:
    return [t for t in _store["tables"] if t.get("selected", False)]


# ── Write helpers (called by API endpoints) ───────────────────────────────────

def set_table_selected(table_name: str, selected: bool):
    for t in _store["tables"]:
        if t["table"] == table_name:
            t["selected"] = selected
            logger.info(f"[SchemaStore] '{table_name}' selected={selected}")
            _save_to_disk()
            return


def save_table_metadata(table_name: str, table_desc: str, col_descs: dict):
    """
    Persist user-written descriptions for a table and columns.
    Saves to disk immediately after updating in-memory store.
    """
    for t in _store["tables"]:
        if t["table"] == table_name:
            t["description"] = table_desc
            for c in t["columns"]:
                if c["name"] in col_descs:
                    c["description"] = col_descs[c["name"]]
            logger.info(f"[SchemaStore] Metadata saved for '{table_name}'")
            _save_to_disk()
            return


# ── Schema context builders (used by agents) ──────────────────────────────────

def get_schema_context(relevant_tables: list[str] = None) -> str:
    """Build schema context string for LLM prompt. Includes user descriptions."""
    selected = get_selected_tables()
    if not selected:
        return ""
    if relevant_tables:
        filtered = [t for t in selected if t["table"] in relevant_tables]
        selected = filtered if filtered else selected

    context = ""
    for t in selected:
        desc = f" — {t['description']}" if t.get("description") else ""
        context += f"\nTable: {t['table']} ({t.get('row_count', 0):,} rows){desc}\n"
        context += "Columns:\n"
        for c in t.get("columns", []):
            col_desc = f" — {c['description']}" if c.get("description") else ""
            context += f"  - {c['name']} ({c['type']}){col_desc}\n"
    return context


def get_full_schema_context_live() -> str:
    return get_schema_context(relevant_tables=None)


def get_relevant_tables_live(question: str) -> list[str]:
    selected = get_selected_tables()
    if not selected:
        return []
    q = question.lower()
    scores: dict[str, int] = {}
    for t in selected:
        score = 0
        tname = t["table"].lower()
        if tname.replace("_", " ") in q:    score += 10
        if tname in q:                       score += 8
        if t.get("description") and t["description"].lower() in q: score += 5
        for c in t.get("columns", []):
            if c["name"].lower().replace("_", " ") in q: score += 3
            if c.get("description") and c["description"].lower() in q: score += 2
        if score > 0:
            scores[t["table"]] = score
    if not scores:
        return [t["table"] for t in selected]
    return sorted(scores, key=scores.get, reverse=True)