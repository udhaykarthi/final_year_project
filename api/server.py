"""
FastAPI server exposing the live-camera analysis pipeline + auth + DB + alerts.
"""
from __future__ import annotations

import os
import sys
import threading
import time

from fastapi import Depends, FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

# Make project root importable when running `python api/server.py`
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except Exception:
    pass

from core.pipeline import AnalysisPipeline  # noqa: E402
from core.camera_manager import CameraManager  # noqa: E402
from api.websocket_manager import ws_manager  # noqa: E402
from auth.routes import router as auth_router  # noqa: E402
from auth.security import get_current_user, get_current_user_optional  # noqa: E402
from db.mongo import ping as db_ping  # noqa: E402
from db.repository import AnalysisRepo, AlertRepo  # noqa: E402


app = FastAPI(title="Rov-E API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

# ---------------------------------------------------------------------------
# Pipeline (lazy + thread-safe)
# ---------------------------------------------------------------------------
_pipeline: AnalysisPipeline | None = None
_pipeline_lock = threading.Lock()


def get_pipeline() -> AnalysisPipeline:
    global _pipeline
    if _pipeline is None:
        with _pipeline_lock:
            if _pipeline is None:
                use_vlm = os.environ.get("USE_VLM", "1") != "0"
                _pipeline = AnalysisPipeline(use_vision_model=use_vlm)
    return _pipeline


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "db": "up" if db_ping() else "down",
        "camera": "up" if CameraManager.get(0).is_alive() else "down",
        "vision": _vision_status(),
    }


def _vision_status() -> str:
    if _pipeline is None:
        return "not_loaded"
    if _pipeline.vision is not None:
        return "ready"
    return f"unavailable ({_pipeline.vision_error or 'unknown'})"


@app.on_event("startup")
def _on_startup():
    # Warm the camera in the background so the first frame is instant
    try:
        CameraManager.get(0)
        print("[Server] Camera warmed up.")
    except Exception as e:
        print(f"[Server] Camera warm-up failed: {e}")


# ---------------------------------------------------------------------------
# Analyze
# ---------------------------------------------------------------------------
@app.post("/analyze")
async def analyze(
    camera_index: int = 0,
    location: str = "live_camera",
    current=Depends(get_current_user_optional),
):
    try:
        pipeline = get_pipeline()
        with _pipeline_lock:
            result = pipeline.analyze(
                image_path=None,
                location=location,
                camera_index=camera_index,
            )
        result["snapshot_url"] = (
            f"/snapshot/{os.path.basename(result['image_path'])}"
        )
        result["annotated_snapshot_url"] = (
            f"/annotated/{os.path.basename(result['annotated_image_path'])}"
        )

        # Persist analysis (only when logged in)
        analysis_id = None
        if current:
            try:
                analysis_id = AnalysisRepo.save(current["id"], result)
                result["id"] = analysis_id
            except Exception as e:
                print(f"[analyze] DB save failed: {e}")

        # WebSocket broadcast on high risk + log alert in DB
        if result["risk_score"] >= 5:
            await ws_manager.send_analysis_result(result)
            for alert in result.get("alerts", []):
                await ws_manager.send_alert(
                    alert_type=alert,
                    details={"objects": result["objects"], "location": location},
                    risk_score=result["risk_score"],
                )

            if current:
                try:
                    AlertRepo.log(
                        user_id=current["id"],
                        alert_type=", ".join(result["alerts"]) or "high_risk",
                        risk_score=result["risk_score"],
                        channel="ws",
                        status="broadcast",
                        details={
                            "analysis_id": analysis_id,
                            "location": location,
                            "objects": result["objects"],
                        },
                    )
                except Exception as e:
                    print(f"[analyze] Alert log failed: {e}")

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Snapshot serving
# ---------------------------------------------------------------------------
@app.get("/snapshot/{name}")
def snapshot(name: str):
    pipeline = get_pipeline()
    path = os.path.join(pipeline.snapshot_dir, name)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return FileResponse(path, media_type="image/jpeg")


@app.get("/annotated/{name}")
def annotated_snapshot(name: str):
    pipeline = get_pipeline()
    path = os.path.join(pipeline.annotated_dir, name)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Annotated snapshot not found")
    return FileResponse(path, media_type="image/jpeg")


# ---------------------------------------------------------------------------
# Live MJPEG preview (uses shared CameraManager - no contention with /analyze)
# ---------------------------------------------------------------------------
def _mjpeg_generator(camera_index: int = 0):
    cam = CameraManager.get(camera_index)
    boundary = b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
    while True:
        jpg = cam.get_jpeg(quality=70)
        if jpg is None:
            time.sleep(0.05)
            continue
        yield boundary + jpg + b"\r\n"
        time.sleep(0.04)  # ~25 fps


@app.get("/video_feed")
def video_feed(camera_index: int = 0):
    try:
        return StreamingResponse(
            _mjpeg_generator(camera_index),
            media_type="multipart/x-mixed-replace; boundary=frame",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# History / dashboard
# ---------------------------------------------------------------------------
@app.get("/history")
def history(limit: int = 50, current=Depends(get_current_user)):
    return {"items": AnalysisRepo.list_for_user(current["id"], limit=limit)}


@app.get("/history/{analysis_id}")
def history_get(analysis_id: str, current=Depends(get_current_user)):
    doc = AnalysisRepo.get(analysis_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    if doc.get("user_id") and str(doc["user_id"]) != current["id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    return doc


@app.get("/alerts")
def alerts_list(limit: int = 50, current=Depends(get_current_user)):
    return {"items": AlertRepo.list_for_user(current["id"], limit=limit)}


@app.get("/dashboard/stats")
def dashboard_stats(current=Depends(get_current_user)):
    return AnalysisRepo.stats_for_user(current["id"])


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------
@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except Exception:
        ws_manager.disconnect(websocket)


@app.get("/stats")
def get_stats():
    pipeline = get_pipeline()
    return {
        "anomaly_stats": pipeline.anomaly_detector.get_statistics(),
        "alert_history": ws_manager.get_alert_history(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=False)
