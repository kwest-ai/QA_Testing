import json
import os
from datetime import datetime

class Recorder:
    def __init__(self, log_path="memory/history.json"):
        self.log_path = log_path
        self.history = []
        if os.path.exists(log_path):
            with open(log_path) as f:
                self.history = json.load(f)

    def record(self, step_number, action_json, verdict, timestamp=None):
        if not timestamp:
            timestamp = datetime.utcnow().isoformat()

        entry = {
            "step": step_number,
            "timestamp": timestamp,
            "action": json.loads(action_json),
            "result": verdict
        }

        self.history.append(entry)
        self._save()

    def _save(self):
        with open(self.log_path, "w") as f:
            json.dump(self.history, f, indent=2)

    def get_history(self):
        return self.history 