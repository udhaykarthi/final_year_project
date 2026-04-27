"""
FastAPI server exposing the live-camera analysis pipeline.

Endpoints:
    GET  /health         -> simple status
    POST /analyze        -> capture one webcam frame and return full analysis
    GET  /snapshot/{name}-> serve a captured frame image
    GET  /video_feed     -> MJPEG live preview (optional, used by the React UI)
"""

import os
import sys
import threading
import time

import cv2
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
# Make project root importable when running `python api/server.py`
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.pipeline import AnalysisPipeline  # noqa: E402


app = FastAPI(title="Vision Safety API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "time": time.strftime("%Y-%m-%d %H:%M:%S")}


@app.post("/analyze")
def analyze(camera_index: int = 0, location: str = "live_camera"):
    try:
        pipeline = get_pipeline()
        with _pipeline_lock:
            result = pipeline.analyze(
                image_path=None,
                location=location,
                camera_index=camera_index,
            )
        # Add a URL the frontend can use to display the captured frame
        result["snapshot_url"] = (
            f"/snapshot/{os.path.basename(result['image_path'])}"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/snapshot/{name}")
def snapshot(name: str):
    pipeline = get_pipeline()
    path = os.path.join(pipeline.snapshot_dir, name)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return FileResponse(path, media_type="image/jpeg")


# ---------------------------------------------------------------------------
# Optional MJPEG live preview (so the UI can show the camera feed)
# ---------------------------------------------------------------------------
def _mjpeg_generator(camera_index: int = 0):
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap.release()
        raise RuntimeError(f"Cannot open camera {camera_index}")
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if not ok:
                continue
            chunk = buf.tobytes()
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + chunk + b"\r\n")
    finally:
        cap.release()


@app.get("/video_feed")
def video_feed(camera_index: int = 0):
    try:
        return StreamingResponse(
            _mjpeg_generator(camera_index),
            media_type="multipart/x-mixed-replace; boundary=frame",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=False)

