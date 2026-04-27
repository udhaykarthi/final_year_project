# 🛡️ Vision Safety System — Live Camera + React UI

Real-time scene safety analyzer:
- **YOLOv8** for object detection
- **Qwen2-VL** for natural-language scene description (optional)
- Rule-based **event detection** + **risk scoring**
- **FastAPI** backend with live webcam capture
- **React** frontend with live preview + results page

---

## 1. Backend (Python + FastAPI)

Activate the existing venv and start the API:

```powershell
cd C:\Projects\final_year_project
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt   # first time only
python api\server.py
```

Server runs on `http://localhost:8000`.

To skip the heavy Qwen vision model (faster startup, no GPU/VRAM needed):

```powershell
$env:USE_VLM="0"; python api\server.py
```

### Endpoints
| Method | Path                | Description                                   |
|--------|---------------------|-----------------------------------------------|
| GET    | `/health`           | Health check                                  |
| POST   | `/analyze`          | Capture 1 webcam frame + run full pipeline    |
| GET    | `/snapshot/{name}`  | Serve a captured frame                        |
| GET    | `/video_feed`       | MJPEG live preview                            |

---

## 2. Frontend (React)

```powershell
cd my-react-app
npm install     # installs react-router-dom + everything else
npm start
```

Opens at `http://localhost:3000`.

Flow:
1. **Home page** shows the live MJPEG webcam feed and a **Run Detection** button.
2. Clicking it calls `POST /analyze`, which captures one frame and runs the full pipeline.
3. App navigates to **`/results`** showing snapshot, risk score, alerts, objects, vision description, and full scene history.

To point the UI at a different backend host:
```powershell
$env:REACT_APP_API_BASE="http://192.168.1.50:8000"; npm start
```

---

## 3. Standalone CLI Test (no React, no API)

```powershell
python test\test_image.py        # original sample image flow
python -c "from core.pipeline import AnalysisPipeline; AnalysisPipeline(use_vision_model=False).analyze()"
```

---

## 4. Project Layout

```
api/             FastAPI server (server.py)
core/            pipeline.py + event_detector / risk_engine / scene_analyzer
detectors/       YOLOv8 wrapper
model/           Qwen2-VL wrapper
memory/          in-memory scene history
trackers/        ByteTrack-based tracker (for video extension)
snapshots/       captured webcam frames (auto-created)
my-react-app/    React UI (Home + Results pages)
```

---

## 5. Notes
- First request after server start is slow (YOLO + Qwen weights load lazily).
- `USE_VLM=0` lets you demo without the 2B-param vision model.
- Webcam uses index `0` (DirectShow on Windows). Pass `?camera_index=1` to `/analyze` or `/video_feed` to switch cameras.

