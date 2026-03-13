class SceneAnalyzer:

    def parse_scene(self, description):

        scene_data = {
            "people": 0,
            "objects": [],
            "risk_level": "low"
        }

        text = description.lower()

        if "person" in text or "people" in text:
            scene_data["people"] += 1

        if "knife" in text or "weapon" in text:
            scene_data["risk_level"] = "high"

        if "fire" in text or "smoke" in text:
            scene_data["risk_level"] = "critical"

        scene_data["objects"].append(description)

        return scene_data