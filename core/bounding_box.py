"""
Bounding box utilities for object visualization.

Draws bounding boxes and labels on detected objects.
Returns image with annotations and object coordinates for frontend.
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple
from ultralytics import YOLO


class BoundingBoxAnnotator:
    """Draw bounding boxes on detected objects."""

    # Color palette (BGR format for OpenCV)
    COLORS = {
        "person": (0, 255, 0),      # Green
        "car": (255, 0, 0),         # Blue
        "knife": (0, 0, 255),       # Red
        "gun": (0, 0, 255),         # Red
        "fire": (0, 165, 255),      # Orange
        "smoke": (128, 128, 128),   # Gray
        "default": (255, 255, 0),   # Cyan
    }

    def __init__(self, model: YOLO = None):
        self.model = model

    def annotate(self, image_path: str, objects_with_boxes: List[Dict]) -> Tuple[np.ndarray, List[Dict]]:
        """
        Draw bounding boxes on image.

        Args:
            image_path: Path to image file
            objects_with_boxes: List of dicts with keys: label, bbox, confidence

        Returns:
            annotated_image: Image with bounding boxes drawn
            box_data: List of box info for frontend rendering
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image: {image_path}")

        box_data = []

        for obj in objects_with_boxes:
            label = obj.get("label", "unknown")
            bbox = obj.get("bbox", [0, 0, 100, 100])
            confidence = obj.get("confidence", 0.0)

            x1, y1, x2, y2 = map(int, bbox)

            # Get color for this object type
            color = self.COLORS.get(label, self.COLORS["default"])

            # Draw rectangle
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

            # Draw label background
            label_text = f"{label} {confidence:.2f}"
            (text_width, text_height), baseline = cv2.getTextSize(
                label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )

            cv2.rectangle(
                image,
                (x1, y1 - text_height - baseline - 5),
                (x1 + text_width, y1),
                color,
                cv2.FILLED
            )

            # Draw label text
            cv2.putText(
                image,
                label_text,
                (x1, y1 - baseline - 1),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                1
            )

            # Store box data for frontend
            box_data.append({
                "label": label,
                "confidence": round(confidence, 3),
                "bbox": {
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "width": x2 - x1,
                    "height": y2 - y1
                },
                "color": self._rgb_to_hex(color)
            })

        return image, box_data

    def _rgb_to_hex(self, bgr_color: Tuple[int, int, int]) -> str:
        """Convert BGR color to hex string for CSS."""
        r, g, b = bgr_color[2], bgr_color[1], bgr_color[0]
        return f"#{r:02x}{g:02x}{b:02x}"

    def get_boxes_from_yolo(self, image_path: str) -> List[Dict]:
        """
        Run YOLO detection and extract bounding boxes.

        Returns list of dicts with label, bbox, confidence.
        """
        if self.model is None:
            self.model = YOLO("yolov8n.pt")

        results = self.model(image_path)
        objects_with_boxes = []

        for r in results:
            boxes = r.boxes
            if boxes is None:
                continue

            for box in boxes:
                cls_id = int(box.cls[0])
                label = self.model.names[cls_id]
                confidence = float(box.conf[0])
                bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]

                objects_with_boxes.append({
                    "label": label,
                    "bbox": bbox,
                    "confidence": confidence
                })

        return objects_with_boxes
