from ultralytics import YOLO
import cv2

class ObjectDetector:

    def __init__(self):
        print("Loading YOLO model...")
        self.model = YOLO("yolov8n.pt")
        print("YOLO ready")

    def detect(self, image_path):

        results = self.model(image_path)

        objects = []

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = self.model.names[cls_id]
                objects.append(label)

        return objects