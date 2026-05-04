"""High-level repositories that wrap MongoDB collections."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

from db.mongo import get_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _oid(value: str | ObjectId | None) -> Optional[ObjectId]:
    if value is None:
        return None
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(value)
    except Exception:
        return None


def _serialize(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if doc is None:
        return None
    out = dict(doc)
    if "_id" in out:
        out["id"] = str(out.pop("_id"))
    if "user_id" in out and isinstance(out["user_id"], ObjectId):
        out["user_id"] = str(out["user_id"])
    return out


def _serialize_many(docs):
    return [_serialize(d) for d in docs]


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
class UserRepo:
    @staticmethod
    def create(email: str, password_hash: str, name: str = "",
               phone: str = "") -> Dict[str, Any]:
        db = get_db()
        doc = {
            "email": email.lower().strip(),
            "password_hash": password_hash,
            "name": name,
            "phone": phone,
            "created_at": datetime.now(timezone.utc),
        }
        res = db.users.insert_one(doc)
        doc["_id"] = res.inserted_id
        return _serialize(doc)

    @staticmethod
    def find_by_email(email: str) -> Optional[Dict[str, Any]]:
        return get_db().users.find_one({"email": email.lower().strip()})

    @staticmethod
    def find_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        oid = _oid(user_id)
        if oid is None:
            return None
        return _serialize(get_db().users.find_one({"_id": oid}))

    @staticmethod
    def update_phone(user_id: str, phone: str) -> bool:
        oid = _oid(user_id)
        if oid is None:
            return False
        res = get_db().users.update_one({"_id": oid}, {"$set": {"phone": phone}})
        return res.modified_count > 0


# ---------------------------------------------------------------------------
# Analyses
# ---------------------------------------------------------------------------
class AnalysisRepo:
    @staticmethod
    def save(user_id: Optional[str], result: Dict[str, Any]) -> str:
        db = get_db()
        doc = {
            "user_id": _oid(user_id),
            "timestamp": datetime.now(timezone.utc),
            "location": result.get("location"),
            "objects": result.get("objects", []),
            "object_counts": result.get("object_counts", {}),
            "alerts": result.get("alerts", []),
            "anomalies": result.get("anomalies", []),
            "risk_score": int(result.get("risk_score", 0)),
            "risk_reasons": result.get("risk_reasons", []),
            "description": result.get("description", ""),
            "snapshot_url": result.get("snapshot_url"),
            "annotated_snapshot_url": result.get("annotated_snapshot_url"),
            "image_filename": _basename(result.get("image_path")),
        }
        res = db.analyses.insert_one(doc)
        return str(res.inserted_id)

    @staticmethod
    def list_for_user(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        oid = _oid(user_id)
        if oid is None:
            return []
        cursor = (get_db().analyses
                  .find({"user_id": oid})
                  .sort("timestamp", -1)
                  .limit(limit))
        return _serialize_many(cursor)

    @staticmethod
    def get(analysis_id: str) -> Optional[Dict[str, Any]]:
        oid = _oid(analysis_id)
        if oid is None:
            return None
        return _serialize(get_db().analyses.find_one({"_id": oid}))

    @staticmethod
    def stats_for_user(user_id: str) -> Dict[str, Any]:
        oid = _oid(user_id)
        if oid is None:
            return {"total": 0, "high_risk": 0, "alerts": 0, "avg_risk": 0.0}
        db = get_db()
        total = db.analyses.count_documents({"user_id": oid})
        high_risk = db.analyses.count_documents({"user_id": oid, "risk_score": {"$gte": 5}})
        # Aggregate average risk and alert count
        pipeline = [
            {"$match": {"user_id": oid}},
            {"$group": {
                "_id": None,
                "avg_risk": {"$avg": "$risk_score"},
                "alerts": {"$sum": {"$size": {"$ifNull": ["$alerts", []]}}},
            }},
        ]
        agg = list(db.analyses.aggregate(pipeline))
        avg_risk = float(agg[0]["avg_risk"]) if agg else 0.0
        alerts = int(agg[0]["alerts"]) if agg else 0
        return {
            "total": total,
            "high_risk": high_risk,
            "alerts": alerts,
            "avg_risk": round(avg_risk, 2),
        }


# ---------------------------------------------------------------------------
# Alerts (separate log of dispatched alerts: SMS sent, etc.)
# ---------------------------------------------------------------------------
class AlertRepo:
    @staticmethod
    def log(user_id: Optional[str], alert_type: str, risk_score: int,
            channel: str, status: str, details: Dict[str, Any]) -> str:
        db = get_db()
        doc = {
            "user_id": _oid(user_id),
            "timestamp": datetime.now(timezone.utc),
            "alert_type": alert_type,
            "risk_score": int(risk_score),
            "channel": channel,
            "status": status,
            "details": details,
        }
        res = db.alerts.insert_one(doc)
        return str(res.inserted_id)

    @staticmethod
    def list_for_user(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        oid = _oid(user_id)
        if oid is None:
            return []
        cursor = (get_db().alerts
                  .find({"user_id": oid})
                  .sort("timestamp", -1)
                  .limit(limit))
        return _serialize_many(cursor)


def _basename(path):
    if not path:
        return None
    import os
    return os.path.basename(path)

