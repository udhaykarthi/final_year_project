class RiskEngine:

    def calculate(self, objects, alerts):

        score = 0
        reasons = []

        # weapon
        if "gun" in objects or "knife" in objects:
            score += 5
            reasons.append("Weapon detected")

        # fire
        if "fire" in objects or "smoke" in objects:
            score += 6
            reasons.append("Fire detected")

        # multiple people
        if objects.count("person") >= 3:
            score += 2
            reasons.append("Group formation")

        # alerts from event detector
        if alerts:
            score += len(alerts) * 2
            reasons.extend(alerts)

        # normalize
        if score > 10:
            score = 10

        return {
            "risk_score": score,
            "reasons": reasons
        }