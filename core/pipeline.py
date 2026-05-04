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
from core.anomaly_detector import AnomalyDetector
from core.bounding_box import BoundingBoxAnnotator
from core.camera_manager import CameraManager
from memory.scene_memory import SceneMemory


class AnalysisPipeline:
    def __init__(self, use_vision_model: bool = True):
        print("[Pipeline] Initializing components...")

        self.detector = ObjectDetector()
        self.event_detector = EventDetector()
        self.risk_engine = RiskEngine()
        self.analyzer = SceneAnalyzer()
        self.memory = SceneMemory()
        self.anomaly_detector = AnomalyDetector()
        self.box_annotator = BoundingBoxAnnotator(self.detector.model)

        self.vision = None
        self.vision_error = None
        self.use_vision_model = use_vision_model

        if use_vision_model:
            self._load_vision_model()

        # Cache snapshots dir
        self.snapshot_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "snapshots",
        )
        self.annotated_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "snapshots",
            "annotated",
        )
        os.makedirs(self.snapshot_dir, exist_ok=True)
        os.makedirs(self.annotated_dir, exist_ok=True)

        print("[Pipeline] Ready.")

    # ------------------------------------------------------------------
    # Vision model lifecycle
    # ------------------------------------------------------------------
    def _load_vision_model(self):
        try:
            from model.vision_qwen import VisionModel
            self.vision = VisionModel()
            self.vision_error = None
        except Exception as e:
            print(f"[Pipeline] Vision model load failed: {e}")
            self.vision = None
            self.vision_error = str(e)

    # ------------------------------------------------------------------
    # Camera capture (uses shared CameraManager - no contention)
    # ------------------------------------------------------------------
    def capture_frame(self, camera_index: int = 0):
        """Grab the latest frame from the shared camera and save it."""
        cam = CameraManager.get(camera_index)
        frame = cam.get_frame(timeout=3.0)
        if frame is None:
            raise RuntimeError(
                f"Could not read frame from camera {camera_index}. "
                "Check that a webcam is connected."
            )
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

        # 1. YOLO objects with bounding boxes
        objects_with_boxes = self.box_annotator.get_boxes_from_yolo(image_path)
        objects = [obj["label"] for obj in objects_with_boxes]
        box_data = [obj for obj in objects_with_boxes]

        # 2. Vision-language description (instruction-tuned)
        description = ""
        vision_status = "ok"
        if not self.use_vision_model:
            vision_status = "disabled_by_config"
        else:
            # Auto-recover if a previous load failed
            if self.vision is None:
                self._load_vision_model()
            if self.vision is not None:
                try:
                    description = self.vision.analyze_image(image_path)
                except Exception as e:
                    print(f"[Pipeline] Vision inference failed: {e}")
                    vision_status = f"error: {e}"
                    description = ""
            else:
                vision_status = f"load_failed: {self.vision_error}"

        # 3. Scene parse
        scene = self.analyzer.parse_scene(description or " ".join(objects))

        # 4. Events
        alerts = self.event_detector.analyze(objects, description or "")

        # 5. Risk
        risk = self.risk_engine.calculate(objects, alerts)

        # 6. Anomaly detection
        self.anomaly_detector.update(objects, risk["risk_score"])
        anomalies = self.anomaly_detector.detect_anomalies(objects, risk["risk_score"])
        anomaly_stats = self.anomaly_detector.get_statistics()

        # 7. Memory
        self.memory.store(location, objects, alerts)

        # 8. Draw bounding boxes on image
        annotated_path = self._save_annotated_image(image_path, box_data)

        result = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "location": location,
            "image_path": image_path,
            "annotated_image_path": annotated_path,
            "objects": objects,
            "object_counts": _counts(objects),
            "bounding_boxes": box_data,
            "description": description,
            "vision_status": vision_status,
            "scene": scene,
            "alerts": alerts,
            "anomalies": anomalies,
            "anomaly_stats": anomaly_stats,
            "risk_score": risk["risk_score"],
            "risk_reasons": risk["reasons"],
            "history": self.memory.get_history(),
        }

        # Pretty terminal print (so terminal still shows the same info)
        _print_result(result)

        return result

    def _save_annotated_image(self, image_path: str, box_data: list) -> str:
        """Save annotated image with bounding boxes."""
        import shutil
        from core.bounding_box import BoundingBoxAnnotator

        annotator = BoundingBoxAnnotator()
        annotated_image, _ = annotator.annotate(image_path, box_data)

        # Generate annotated filename
        basename = os.path.basename(image_path)
        annotated_path = os.path.join(self.annotated_dir, f"annotated_{basename}")

        cv2.imwrite(annotated_path, annotated_image)
        return annotated_path


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

