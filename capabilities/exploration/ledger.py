"""Append-only local experiment records. Database files belong in ignored artifacts."""
import hashlib
import json
import sqlite3
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


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
        payload = canonical(record)
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            if parent is not None and not self.db.execute(
                "SELECT 1 FROM records WHERE id = ?", (parent,)
            ).fetchone():
                raise ValueError("parent must already exist")
            self.db.execute("INSERT INTO records VALUES (?, ?)", (record["id"], payload))
        return record

    def records(self):
        return [json.loads(row[0]) for row in self.db.execute("SELECT payload FROM records ORDER BY rowid")]

    def close(self):
        self.db.close()
