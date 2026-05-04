"""
MongoDB Atlas connection.

Reads credentials from environment variables (loaded from .env via python-dotenv).
Required env:
    MONGODB_URI   - full Atlas connection string
    MONGODB_DB    - database name (defaults to 'rov_e')

The client is created lazily on first call to get_db() so the API can
boot even if Mongo is misconfigured (it will raise only on the first DB op).
"""
from __future__ import annotations

import os
import threading
from typing import Optional

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except Exception:
    pass


_client: Optional[MongoClient] = None
_db: Optional[Database] = None
_lock = threading.Lock()


def _connect() -> Database:
    uri = os.environ.get("MONGODB_URI")
    db_name = os.environ.get("MONGODB_DB", "rov_e")

    if not uri:
        raise RuntimeError(
            "MONGODB_URI is not set. Copy .env.example to .env and add your "
            "MongoDB Atlas connection string."
        )

    client = MongoClient(uri, serverSelectionTimeoutMS=8000, appname="rov-e-api")
    # Force a quick connection check
    client.admin.command("ping")

    db = client[db_name]
    _ensure_indexes(db)
    globals()["_client"] = client
    return db


def _ensure_indexes(db: Database) -> None:
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.analyses.create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
    db.analyses.create_index([("timestamp", DESCENDING)])
    db.alerts.create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
    db.alerts.create_index([("timestamp", DESCENDING)])


def get_db() -> Database:
    global _db
    if _db is None:
        with _lock:
            if _db is None:
                _db = _connect()
    return _db


def ping() -> bool:
    try:
        get_db().command("ping")
        return True
    except Exception:
        return False


def close_db() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None

