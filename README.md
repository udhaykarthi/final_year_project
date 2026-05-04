# 🤖 Rov-E — Real-time Observational Vision Engine

Real-time scene safety analyzer:
- **YOLOv8** for object detection
- **Qwen2-VL** for natural-language scene description (instruction-tuned)
- Rule-based **event detection** + **risk scoring**
- **FastAPI** backend with live webcam capture
- **MongoDB Atlas** for users, analyses, alert logs
- **JWT auth** (register / login)
- **React** dashboard (Live, History, Settings)

---

## 1. Configure environment

A real `.env` is already created in the project root. Required keys:

| Key             | Purpose                                        |
|-----------------|------------------------------------------------|
| `MONGODB_URI`   | Atlas connection string (`mongodb+srv://...`)  |
| `MONGODB_DB`    | Database name (default `rov_e`)                |
| `JWT_SECRET`    | Long random string for signing JWTs            |
| `USE_VLM`       | `0` to skip the Qwen-VL model (faster startup) |

The React app reads `my-react-app/.env`:

```env
REACT_APP_API_BASE=http://localhost:8000
```

---

## 2. Backend (Python + FastAPI)

```powershell
cd C:\Projects\final_year_project
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python api\server.py
```

API runs on `http://localhost:8000`. Interactive docs at `/docs`.

### Endpoints

| Method | Path                  | Auth | Description                                  |
|--------|-----------------------|------|----------------------------------------------|
| GET    | `/health`             | —    | Health (also reports DB status)              |
| POST   | `/auth/register`      | —    | Create user, returns JWT                     |
| POST   | `/auth/login`         | —    | Login (JSON), returns JWT                    |
| GET    | `/auth/me`            | ✓    | Current user profile                         |
| POST   | `/analyze`            | opt  | Capture webcam frame + analyze (saved if logged in) |
| GET    | `/history`            | ✓    | List analyses for user                       |
| GET    | `/history/{id}`       | ✓    | One analysis                                 |
| GET    | `/alerts`             | ✓    | High-risk alert log                          |
| GET    | `/dashboard/stats`    | ✓    | Aggregate stats                              |
| GET    | `/snapshot/{name}`    | —    | Captured frame                               |
| GET    | `/annotated/{name}`   | —    | Annotated frame                              |
| GET    | `/video_feed`         | —    | MJPEG live preview                           |
| WS     | `/ws/alerts`          | —    | Real-time alert push                         |

When `/analyze` produces `risk_score >= 5`:
- alert is broadcast on the WebSocket,
- analysis is stored in `analyses` (if user is signed in),
- a row is added to `alerts`.

---

## 3. Frontend (React)

```powershell
cd my-react-app
npm install
npm start
```

Opens at `http://localhost:3000`.

Pages:
- `/login`, `/register` — auth
- `/dashboard` — stats + recent activity
- `/live` — webcam preview + Run Detection
- `/results` — full scene breakdown after a detection
- `/history` — every saved scene
- `/settings` — account info

---

## 4. Standalone CLI Test (no React, no API)

```powershell
python test\test_image.py
python -c "from core.pipeline import AnalysisPipeline; AnalysisPipeline(use_vision_model=False).analyze()"
```

---

## 5. Project Layout

```
api/             FastAPI server (server.py, websocket_manager.py)
auth/            JWT + bcrypt auth + /auth routes
db/              MongoDB Atlas connection + repositories
core/            pipeline.py + event_detector / risk_engine / scene_analyzer / anomaly / bbox
detectors/       YOLOv8 wrapper
model/           Qwen2-VL wrapper
memory/          in-memory scene history
trackers/        ByteTrack-based tracker
snapshots/       captured webcam frames (auto-created, gitignored)
my-react-app/    React UI (Login, Register, Dashboard, Live, Results, History, Settings)
.env.example     copy to .env and fill in
.env             real values (gitignored)
```

---

## 6. Notes
- First request after server start is slow (YOLO + Qwen weights load lazily).
- Set `USE_VLM=0` to skip the 2B-param vision model (faster boot, no GPU needed).
- Webcam uses index `0` (DirectShow on Windows). Pass `?camera_index=1` to `/analyze` or `/video_feed`.
- DB indexes (`users.email` unique, `analyses.user_id+timestamp`, etc.) are created automatically on first connection.
