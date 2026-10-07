"""Frozen recorded world; policy receives only revealed observations."""
from copy import deepcopy
import math


def validate_world(nodes):
    known, used_parents = {"root"}, set()
    for node in nodes:
        identifier, parent, score = node.get("id"), node.get("parent"), node.get("score")
        if not isinstance(identifier, str) or not identifier.strip() or identifier in known:
            raise ValueError("world ids must be unique nonempty strings excluding root")
        if not isinstance(parent, str) or parent not in known:
            raise ValueError("parent must precede child")
        if parent != "root" and parent in used_parents:
            raise ValueError("nonroot branches must have a single continuation")
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or score < 0:
            raise ValueError("score must be finite and nonnegative")
        known.add(identifier)
        used_parents.add(parent)
    return deepcopy(nodes)


class Replay:
    def __init__(self, nodes):
        self._nodes = validate_world(nodes)
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
