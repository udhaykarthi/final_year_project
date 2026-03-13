class EventDetector:

    def analyze(self, objects, description):

        alerts = []

        text = description.lower()

        # Weapon detection
        if "knife" in objects or "gun" in objects:
            alerts.append("Weapon detected")

        # Fire detection
        if "fire" in objects or "smoke" in objects:
            alerts.append("Fire or smoke detected")

        # Person lying detection
        if "lying" in text or "person on the floor" in text:
            alerts.append("Possible medical emergency")

        # Crowd detection
        if objects.count("person") >= 3:
            alerts.append("Group formation detected")

        # Suspicious object
        if "backpack" in objects and objects.count("person") == 0:
            alerts.append("Unattended bag detected")

        return alerts