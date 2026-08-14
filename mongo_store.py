"""MongoDB mirror for the bot state backup.

The bot keeps its live data in SQLite. Backups are mirrored to two
independent destinations so nothing is ever lost on a restart / redeploy:

    * GitHub  (JSON files, existing engine)
    * MongoDB (this module)

Both are cumulative: a backup only ever adds/updates rows, it never deletes.
Restoring merges every destination back into SQLite.

Environment variables
---------------------
MONGODB_URI       mongodb+srv://user:pass@cluster/...   (required to enable)
MONGODB_DB        database name          (default: quizbot)
MONGO_BACKUP      1/0 master switch      (default: 1)
"""

from __future__ import annotations

import base64
import gzip
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("mongo_store")

MONGODB_URI = (os.getenv("MONGODB_URI") or os.getenv("MONGO_URI") or "").strip()
MONGODB_DB = (os.getenv("MONGODB_DB") or os.getenv("MONGO_DB") or "quizbot").strip() or "quizbot"
MONGO_ENABLED = (os.getenv("MONGO_BACKUP", "1").strip() not in {"0", "false", "False", ""})

_ROWS_PREFIX = "tbl_"
_SNAPSHOTS = "snapshots"
_META = "meta"

_client: Any = None
_db: Any = None
_last_error: str = ""


def configured() -> bool:
    return bool(MONGODB_URI) and MONGO_ENABLED


def last_error() -> str:
    return _last_error


def _connect() -> Any:
    """Return a cached database handle, or None when unavailable."""
    global _client, _db, _last_error
    if not configured():
        return None
    if _db is not None:
        return _db
    try:
        from pymongo import MongoClient  # type: ignore

        _client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=15000,
            socketTimeoutMS=60000,
            retryWrites=True,
            appname="advanced-quiz-bot",
        )
        _client.admin.command("ping")
        _db = _client[MONGODB_DB]
        _last_error = ""
        logger.info("MongoDB connected: db=%s", MONGODB_DB)
    except Exception as exc:  # pragma: no cover - network dependent
        _last_error = str(exc)
        _client = None
        _db = None
        logger.warning("MongoDB unavailable: %s", exc)
    return _db


def ping() -> bool:
    return _connect() is not None


# ------------------------------------------------------------------
# cumulative row storage
# ------------------------------------------------------------------

def push_tables(keyed: Dict[str, List[Tuple[str, Dict[str, Any]]]]) -> Dict[str, Any]:
    """Upsert every (key, row) pair. Returns {"rows": n, "tables": n}."""
    db = _connect()
    if db is None:
        return {"rows": 0, "tables": 0, "ok": False, "error": _last_error or "not configured"}
    from pymongo import UpdateOne  # type: ignore

    total = 0
    tables = 0
    errors: List[str] = []
    now = int(time.time())
    for table, pairs in (keyed or {}).items():
        if not pairs:
            continue
        ops = []
        for key, row in pairs:
            try:
                doc = json.loads(json.dumps(row, ensure_ascii=False, default=str))
            except Exception:
                continue
            ops.append(UpdateOne({"_id": key}, {"$set": {"d": doc, "t": now}}, upsert=True))
        if not ops:
            continue
        coll = db[_ROWS_PREFIX + table]
        saved = 0
        for i in range(0, len(ops), 500):
            try:
                batch = ops[i:i + 500]
                coll.bulk_write(batch, ordered=False)
                saved += len(batch)
            except Exception as exc:
                logger.warning("Mongo bulk_write failed for %s: %s", table, exc)
                errors.append(f"{table}: {exc}")
        total += saved
        if saved:
            tables += 1
    try:
        db[_META].update_one(
            {"_id": "backup"},
            {"$set": {"last_backup": now, "rows": total, "tables": tables}},
            upsert=True,
        )
    except Exception:
        pass
    return {
        "rows": total,
        "tables": tables,
        "ok": not errors,
        "error": "; ".join(errors[:3]),
    }


def load_tables() -> Dict[str, List[Dict[str, Any]]]:
    """Read every stored row back, grouped by table name."""
    db = _connect()
    if db is None:
        return {}
    out: Dict[str, List[Dict[str, Any]]] = {}
    try:
        names = [n for n in db.list_collection_names() if n.startswith(_ROWS_PREFIX)]
    except Exception as exc:
        logger.warning("Mongo list_collection_names failed: %s", exc)
        return {}
    for name in names:
        table = name[len(_ROWS_PREFIX):]
        rows: List[Dict[str, Any]] = []
        try:
            # Oldest first, newest last: the restore merger can then let the
            # latest version win for a stable logical row key.
            for doc in db[name].find({}, {"d": 1, "t": 1}).sort("t", 1):
                data = doc.get("d")
                if isinstance(data, dict):
                    rows.append(data)
        except Exception as exc:
            logger.warning("Mongo read failed for %s: %s", table, exc)
            continue
        if rows:
            out[table] = rows
    return out


# ------------------------------------------------------------------
# snapshots (compressed full payloads)
# ------------------------------------------------------------------

def save_snapshot(stamp: str, tables: Dict[str, Any]) -> bool:
    db = _connect()
    if db is None:
        return False
    try:
        raw = json.dumps(tables, ensure_ascii=False, default=str).encode("utf-8")
        blob = base64.b64encode(gzip.compress(raw, 6)).decode("ascii")
        if len(blob) > 14 * 1024 * 1024:
            logger.warning("Mongo snapshot skipped (too large): %s bytes", len(blob))
            return False
        db[_SNAPSHOTS].update_one(
            {"_id": stamp},
            {"$set": {"gz": blob, "ts": int(time.time()), "raw_size": len(raw)}},
            upsert=True,
        )
        return True
    except Exception as exc:
        logger.warning("Mongo snapshot failed: %s", exc)
        return False


def list_snapshots() -> List[Dict[str, Any]]:
    db = _connect()
    if db is None:
        return []
    out: List[Dict[str, Any]] = []
    try:
        for doc in db[_SNAPSHOTS].find({}, {"ts": 1, "raw_size": 1}).sort("_id", -1).limit(50):
            out.append({
                "name": str(doc.get("_id")),
                "path": f"mongo://{doc.get('_id')}",
                "size": int(doc.get("raw_size") or 0),
                "ts": int(doc.get("ts") or 0),
            })
    except Exception as exc:
        logger.warning("Mongo snapshot list failed: %s", exc)
    return out


def load_snapshot(stamp: str) -> Dict[str, Any]:
    db = _connect()
    if db is None:
        return {}
    try:
        doc = db[_SNAPSHOTS].find_one({"_id": stamp})
        if not doc or not doc.get("gz"):
            return {}
        raw = gzip.decompress(base64.b64decode(doc["gz"]))
        data = json.loads(raw.decode("utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        logger.warning("Mongo snapshot load failed: %s", exc)
        return {}


# ------------------------------------------------------------------
# diagnostics
# ------------------------------------------------------------------

def stats() -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "configured": configured(),
        "connected": False,
        "db": MONGODB_DB,
        "rows": 0,
        "tables": 0,
        "snapshots": 0,
        "storage": 0,
        "last_backup": 0,
        "error": _last_error,
    }
    db = _connect()
    if db is None:
        info["error"] = _last_error or ("not configured" if not configured() else "unavailable")
        return info
    info["connected"] = True
    try:
        for name in db.list_collection_names():
            if not name.startswith(_ROWS_PREFIX):
                continue
            info["tables"] += 1
            info["rows"] += int(db[name].estimated_document_count() or 0)
        info["snapshots"] = int(db[_SNAPSHOTS].estimated_document_count() or 0)
        st = db.command("dbstats")
        info["storage"] = int(st.get("dataSize") or 0)
        meta = db[_META].find_one({"_id": "backup"}) or {}
        info["last_backup"] = int(meta.get("last_backup") or 0)
        info["error"] = ""
    except Exception as exc:
        info["error"] = str(exc)
    return info


def purge_all() -> int:
    """Drop every backup collection (used only by explicit owner action)."""
    db = _connect()
    if db is None:
        return 0
    dropped = 0
    try:
        for name in db.list_collection_names():
            if name.startswith(_ROWS_PREFIX) or name in {_SNAPSHOTS}:
                db[name].drop()
                dropped += 1
    except Exception as exc:
        logger.warning("Mongo purge failed: %s", exc)
    return dropped
