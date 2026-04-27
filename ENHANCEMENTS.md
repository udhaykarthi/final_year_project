# New Enhancements

Three major features added to the Vision Safety System:

---

## 1. Bounding Box Visualization

**Files:** `core/bounding_box.py`

Draws colored bounding boxes around detected objects on the captured image.

- Each object type has a unique color (weapons = red, person = green, fire = orange)
- Boxes include label and confidence score
- Frontend can toggle between raw and annotated images
- Legend shows all detected objects with their colors

**How it works:**
1. YOLO returns bounding box coordinates with each detection
2. `BoundingBoxAnnotator` draws rectangles and labels using OpenCV
3. Annotated image saved to `snapshots/annotated/`
4. Frontend displays with a checkbox toggle

---

## 2. Real-Time WebSocket Alerts

**Files:** `api/websocket_manager.py`

Pushes high-risk alerts to connected clients instantly.

- Clients receive notifications when risk score >= 5
- Live alert banners slide in on the home page
- Connection status indicator (green = connected, red = offline)
- Alert history available via `GET /stats`

**How it works:**
1. Frontend opens WebSocket connection to `/ws/alerts`
2. After each analysis, if risk is high, server broadcasts via `ws_manager.send_alert()`
3. Frontend shows sliding notification for 5 seconds

---

## 3. Anomaly Detection

**Files:** `core/anomaly_detector.py`

Detects unusual patterns by comparing against scene history.

**Detects:**
- New objects appearing suddenly
- Important objects disappearing (person, vehicle)
- Sudden risk score spikes (4+ points)
- Unusual object combinations (person + knife, person + fire)

**How it works:**
1. Maintains rolling history of last 10 observations
2. Builds baseline of common objects
3. Compares each new frame against history
4. Returns list of anomaly alerts

---

## Installation

### Step 1: Install new Python dependencies

```bash
cd G:\rove-phi-3
.\phi3env\Scripts\activate
pip install websockets>=12.0 sqlite-utils>=3.36 aiohttp>=3.9.0
```

### Step 2: Install/update existing dependencies

```bash
pip install -r requirements.txt
```

---

## How to Run

### Backend (with new features)

```bash
cd G:\rove-phi-3
.\phi3env\Scripts\activate
python api\server.py
```

Server runs on `http://localhost:8000`

New endpoints:
- `GET /stats` - Anomaly statistics + alert history
- `GET /annotated/{name}` - Annotated snapshots with bounding boxes
- `WS /ws/alerts` - WebSocket for real-time alerts

### Frontend (with new UI features)

```bash
cd G:\rove-phi-3\my-react-app
npm install
npm start
```

Opens at `http://localhost:3000`

---

## What's New in the UI

### Home Page
- **Connection status** - Green/red dot showing WebSocket connection
- **Live alert banners** - Slide in from right when high-risk events detected

### Results Page
- **Bounding box toggle** - Checkbox to switch between raw/annotated images
- **Object legend** - Shows detected objects with color codes
- **Anomalies card** - Displays anomaly detection results
- **Stats** - Shows observation count and average risk

---

## File Summary

| New File | Purpose |
|----------|---------|
| `core/bounding_box.py` | Draw boxes on detected objects |
| `core/anomaly_detector.py` | Pattern-based anomaly detection |
| `api/websocket_manager.py` | Real-time alert broadcasting |

| Modified File | Changes |
|---------------|---------|
| `core/pipeline.py` | Integrated bounding boxes + anomaly detection |
| `api/server.py` | Added WebSocket endpoint + annotated image route |
| `my-react-app/src/App.js` | WebSocket connection + live alerts |
| `my-react-app/src/Results.js` | Bounding box toggle + anomaly display |
| `my-react-app/src/App.css` | New styles for all features |
| `requirements.txt` | Added websockets, sqlite-utils, aiohttp |
