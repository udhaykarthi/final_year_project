"""
Unified analysis pipeline.

Captures one frame from a webcam (or accepts an image path), runs:
  - YOLO object detection
  - Qwen vision reasoning (optional / lazy)
  - Event detection (rules)
  - Risk scoring
  - Memory store
and returns a single result dict suitable for JSON / UI display.
"""

import os
import time
import cv2

from detectors.object_detector import ObjectDetector
from core.event_detector import EventDetector
from core.risk_engine import RiskEngine
from core.scene_analyzer import SceneAnalyzer
from memory.scene_memory import SceneMemory


class AnalysisPipeline:
    def __init__(self, use_vision_model: bool = True):
        print("[Pipeline] Initializing components...")

        self.detector = ObjectDetector()
        self.event_detector = EventDetector()
        self.risk_engine = RiskEngine()
        self.analyzer = SceneAnalyzer()
        self.memory = SceneMemory()

        self.vision = None
        self.use_vision_model = use_vision_model

        if use_vision_model:
            try:
                # Lazy import so app can still run without heavy VLM deps
                from model.vision_qwen import VisionModel
                self.vision = VisionModel()
            except Exception as e:
                print(f"[Pipeline] Vision model disabled: {e}")
                self.vision = None

        # Cache snapshots dir
        self.snapshot_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "snapshots",
        )
        os.makedirs(self.snapshot_dir, exist_ok=True)

        print("[Pipeline] Ready.")

    # ------------------------------------------------------------------
    # Camera capture
    # ------------------------------------------------------------------
    def capture_frame(self, camera_index: int = 0):
        """Open the webcam, grab a single frame, save it, return path."""
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)

        if not cap.isOpened():
            cap.release()
            raise RuntimeError(
                f"Could not open camera index {camera_index}. "
                "Check that a webcam is connected and not in use."
            )

        # Warm-up: some cameras need a few frames before exposure stabilizes
        frame = None
        for _ in range(5):
            ok, frame = cap.read()
            if not ok:
                continue

        cap.release()

        if frame is None:
            raise RuntimeError("Camera opened but failed to read a frame.")

        ts = time.strftime("%Y%m%d_%H%M%S")
        path = os.path.join(self.snapshot_dir, f"frame_{ts}.jpg")
        cv2.imwrite(path, frame)
        return path

    # ------------------------------------------------------------------
    # Main entry
    # ------------------------------------------------------------------
    def analyze(self, image_path: str = None, location: str = "live_camera",
                camera_index: int = 0):
        """
        Run the full pipeline. If image_path is None, captures a webcam frame.
        Returns a JSON-serializable dict.
        """
        if image_path is None:
            image_path = self.capture_frame(camera_index=camera_index)

        print(f"[Pipeline] Analyzing: {image_path}")

        # 1. YOLO objects
        objects = self.detector.detect(image_path)

        # 2. Vision-language description (optional)
        description = ""
        if self.vision is not None:
            try:
                description = self.vision.analyze_image(image_path)
            except Exception as e:
                description = f"[vision model error: {e}]"

        # 3. Scene parse
        scene = self.analyzer.parse_scene(description or " ".join(objects))

        # 4. Events
        alerts = self.event_detector.analyze(objects, description or "")

        # 5. Risk
        risk = self.risk_engine.calculate(objects, alerts)

        # 6. Memory
        self.memory.store(location, objects, alerts)

        result = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "location": location,
            "image_path": image_path,
            "objects": objects,
            "object_counts": _counts(objects),
            "description": description,
            "scene": scene,
            "alerts": alerts,
            "risk_score": risk["risk_score"],
            "risk_reasons": risk["reasons"],
            "history": self.memory.get_history(),
        }

        # Pretty terminal print (so terminal still shows the same info)
        _print_result(result)

        return result


def _counts(items):
    out = {}
    for x in items:
        out[x] = out.get(x, 0) + 1
    return out


def _print_result(r):
    print("\n===== ANALYSIS RESULT =====")
    print(f"Time      : {r['timestamp']}")
    print(f"Location  : {r['location']}")
    print(f"Image     : {r['image_path']}")
    print(f"Objects   : {r['objects']}")
    print(f"Counts    : {r['object_counts']}")
    print(f"Alerts    : {r['alerts'] if r['alerts'] else 'None'}")
    print(f"Risk      : {r['risk_score']} -> {r['risk_reasons']}")
    if r["description"]:
        print("Description:")
        print(r["description"])
    print("===========================\n")

