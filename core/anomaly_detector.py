"""
Anomaly detection module.

Detects unusual patterns by comparing current scene against historical data.
Flags anomalies like:
- Sudden appearance/disappearance of objects
- Unusual object combinations
- Rapid risk score changes
"""

import time
from collections import defaultdict


class AnomalyDetector:
    def __init__(self, history_window: int = 10):
        self.history_window = history_window
        self.object_history = []
        self.risk_history = []
        self.baseline_objects = defaultdict(int)
        self.last_update = time.time()

    def update(self, objects: list, risk_score: int):
        """Add current observation to history."""
        self.object_history.append({
            "timestamp": time.time(),
            "objects": objects,
            "risk_score": risk_score
        })

        self.risk_history.append(risk_score)

        # Update baseline (running average of object counts)
        for obj in objects:
            self.baseline_objects[obj] += 1

        # Trim history to window size
        if len(self.object_history) > self.history_window:
            self.object_history = self.object_history[-self.history_window:]
        if len(self.risk_history) > self.history_window:
            self.risk_history = self.risk_history[-self.history_window:]

    def detect_anomalies(self, objects: list, risk_score: int) -> list:
        """
        Compare current observation against history.
        Returns list of anomaly alerts.
        """
        anomalies = []

        if len(self.object_history) < 3:
            # Not enough history yet
            return anomalies

        # 1. Check for sudden object appearance
        prev_objects = set()
        if self.object_history:
            prev_objects = set(self.object_history[-1]["objects"])

        current_objects = set(objects)
        new_objects = current_objects - prev_objects
        disappeared_objects = prev_objects - current_objects

        for obj in new_objects:
            if obj not in self.baseline_objects or self.baseline_objects[obj] == 0:
                anomalies.append(f"New object appeared: {obj}")

        for obj in disappeared_objects:
            if obj in ["person", "vehicle"]:
                anomalies.append(f"Important object disappeared: {obj}")

        # 2. Check for sudden risk spike
        if len(self.risk_history) >= 2:
            avg_risk = sum(self.risk_history[:-1]) / len(self.risk_history[:-1])
            if risk_score - avg_risk >= 4:
                anomalies.append(f"Sudden risk spike: {avg_risk:.1f} -> {risk_score}")

        # 3. Check for unusual object combinations
        unusual_combos = [
            (["person", "knife"], "Person with potential weapon"),
            (["person", "fire"], "Person near fire"),
            (["backpack", "person"], "Unattended bag near person"),
        ]

        for combo, message in unusual_combos:
            if all(item in current_objects for item in combo):
                anomalies.append(f"Unusual combination: {message}")

        return anomalies

    def get_statistics(self) -> dict:
        """Return basic statistics about observed history."""
        if not self.object_history:
            return {"observations": 0}

        all_objects = []
        for obs in self.object_history:
            all_objects.extend(obs["objects"])

        return {
            "observations": len(self.object_history),
            "unique_objects": len(set(all_objects)),
            "avg_risk": sum(self.risk_history) / len(self.risk_history) if self.risk_history else 0,
            "max_risk": max(self.risk_history) if self.risk_history else 0,
        }
