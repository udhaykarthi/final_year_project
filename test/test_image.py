from model.vision_qwen import VisionModel
from core.scene_analyzer import SceneAnalyzer
from detectors.object_detector import ObjectDetector

vision = VisionModel()
detector = ObjectDetector()
analyzer = SceneAnalyzer()

image_path = "images/test.jpg"

# YOLO detection
objects = detector.detect(image_path)

print("\nDetected Objects:")
print(objects)

# Vision reasoning
description = vision.analyze_image(image_path)

print("\nScene Description:")
print(description)

scene = analyzer.parse_scene(description)

print("\nParsed Scene:")
print(scene)