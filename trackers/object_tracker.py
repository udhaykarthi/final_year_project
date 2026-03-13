from ultralytics import YOLO

class ObjectTracker:

    def __init__(self):
        print("Loading YOLO tracker...")
        self.model = YOLO("yolov8n.pt")

    def track(self, source):

        results = self.model.track(
            source=source,
            persist=True,
            tracker="bytetrack.yaml"
        )

        tracked_objects = []

        for r in results:
            boxes = r.boxes

            if boxes is None:
                continue

            for box in boxes:
                cls_id = int(box.cls[0])
                label = self.model.names[cls_id]

                track_id = int(box.id[0]) if box.id is not None else None

                tracked_objects.append({
                    "id": track_id,
                    "label": label
                })

        return tracked_objects