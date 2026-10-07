"""Frozen recorded world; policy receives only revealed observations."""
from copy import deepcopy


class Replay:
    def __init__(self, nodes):
        self._nodes = deepcopy(nodes)
        self._seen = [{"id": "root", "parent": None, "score": 0.0}]
        self.rounds = 0

    def observation(self):
        return deepcopy(self._seen)

    def step(self, parents):
        seen = {n["id"] for n in self._seen}
        additions = []
        for parent in parents:
            options = [n for n in self._nodes if n["parent"] == parent and n["id"] not in seen]
            if not options:
                return {"status": "unsupported", "revealed": []}
            additions.append(options[0])
        self._seen.extend(deepcopy(additions))
        self.rounds += bool(parents)
        return {"status": "ok", "revealed": deepcopy(additions)}
