import time

class SceneMemory:

    def __init__(self):
        self.history = []

    def store(self, location, objects, alerts):

        entry = {
            "timestamp": time.strftime("%H:%M:%S"),
            "location": location,
            "objects": objects,
            "alerts": alerts
        }

        self.history.append(entry)

    def get_history(self):
        return self.history

    def print_history(self):

        print("\nScene History\n----------------")

        for entry in self.history:
            print(entry)