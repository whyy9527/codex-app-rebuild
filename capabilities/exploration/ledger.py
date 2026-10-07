"""Append-only local experiment records. Database files belong in ignored artifacts."""
import hashlib
import json
import sqlite3
from copy import deepcopy
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def verify_records(records):
    prefix, known, legacy = [], set(), 0
    sealed = False
    for record in records:
        identifier, parent = record.get("id"), record.get("parent")
        if identifier in known or (parent is not None and parent not in known):
            raise ValueError("invalid record ancestry")
        content = {k: v for k, v in record.items() if k != "_integrity"}
        seal = record.get("_integrity")
        if seal is None:
            if sealed:
                raise ValueError("missing seal after sealed records")
            legacy += 1
        else:
            sealed = True
            if seal != {"prefix": digest(prefix), "content": digest(content)}:
                raise ValueError("record or prefix integrity mismatch")
        evaluation = record.get("evaluation")
        if evaluation:
            if evaluation["source_digest"] != digest(evaluation["source_files"]):
                raise ValueError("source manifest mismatch")
            if evaluation["output_sha256"] != hashlib.sha256(evaluation["output"].encode()).hexdigest():
                raise ValueError("output mismatch")
            expected = digest({"command": evaluation["command"], "tests": {
                k: v for k, v in evaluation["source_files"].items() if k.startswith("tests/")}})
            if evaluation["evaluator_digest"] != expected:
                raise ValueError("evaluator mismatch")
        prefix.append(record)
        known.add(identifier)
    return {"records": len(records), "legacy_unsealed": legacy, "digest": digest(records)}


class Ledger:
    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, timeout=10)
        self.db.execute("CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")

    def append(self, record):
        if not isinstance(record.get("id"), str) or not record["id"].strip():
            raise ValueError("record id must be a nonempty string")
        parent = record.get("parent")
        if parent is not None and (not isinstance(parent, str) or parent == record["id"]):
            raise ValueError("invalid parent")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            prefix = self.records()
            verify_records(prefix)
            if parent is not None and not self.db.execute(
                "SELECT 1 FROM records WHERE id = ?", (parent,)
            ).fetchone():
                raise ValueError("parent must already exist")
            record = deepcopy(record)
            record.pop("_integrity", None)
            record["_integrity"] = {"prefix": digest(prefix), "content": digest(record)}
            payload = canonical(record)
            self.db.execute("INSERT INTO records VALUES (?, ?)", (record["id"], payload))
        return record

    def records(self):
        return [json.loads(row[0]) for row in self.db.execute("SELECT payload FROM records ORDER BY rowid")]

    def close(self):
        self.db.close()

    def verify(self):
        return verify_records(self.records())
