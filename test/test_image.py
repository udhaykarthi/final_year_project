import sys
import os

# allow project imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from model.vision_qwen import VisionModel
from detectors.object_detector import ObjectDetector
from core.scene_analyzer import SceneAnalyzer
from core.event_detector import EventDetector
from core.risk_engine import RiskEngine
from memory.scene_memory import SceneMemory


def main():

    print("\n===== INITIALIZING SYSTEM =====")

    vision = VisionModel()
    detector = ObjectDetector()
    analyzer = SceneAnalyzer()
    event_detector = EventDetector()
    risk_engine = RiskEngine()
    memory = SceneMemory()

    image_path = "images/test.jpg"
    location = "living_room"

    print("\n===== OBJECT DETECTION =====")

    objects = detector.detect(image_path)
    print("Detected Objects:", objects)

    print("\n===== VISION REASONING =====")

    description = vision.analyze_image(image_path)
    print("Scene Description:")
    print(description)

    print("\n===== SCENE ANALYSIS =====")

    scene = analyzer.parse_scene(description)
    print(scene)

    print("\n===== EVENT DETECTION =====")

    alerts = event_detector.analyze(objects, description)
    print("Alerts:", alerts if alerts else "No threats detected")

    print("\n===== RISK SCORING =====")

    risk = risk_engine.calculate(objects, alerts)
    print("Risk Score:", risk["risk_score"])
    print("Reasons:", risk["reasons"])

    print("\n===== MEMORY STORE =====")

    memory.store(location, objects, alerts)

    print("\n===== SCENE HISTORY =====")

    memory.print_history()


if __name__ == "__main__":
    main()