from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, state_dir: Path):
        self.state_dir = state_dir.resolve()
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.state_dir / "skillkeeper.sqlite3"
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._migrate()

    def close(self) -> None:
        self.connection.close()

    def _migrate(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS skills (
                name TEXT NOT NULL,
                path TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                dependencies_json TEXT NOT NULL,
                issues_json TEXT NOT NULL,
                scanned_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT NOT NULL,
                target_path TEXT NOT NULL,
                suite TEXT NOT NULL,
                score REAL NOT NULL,
                passed INTEGER NOT NULL,
                total INTEGER NOT NULL,
                results_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS candidates (
                candidate_id TEXT PRIMARY KEY,
                skill_name TEXT NOT NULL,
                baseline_path TEXT NOT NULL,
                candidate_path TEXT NOT NULL,
                baseline_hash TEXT NOT NULL,
                candidate_hash TEXT NOT NULL,
                before_score REAL NOT NULL,
                after_score REAL NOT NULL,
                holdout_score REAL NOT NULL,
                status TEXT NOT NULL,
                manifest_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                skill_name TEXT,
                details_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        self.connection.commit()

    def upsert_skill(self, record: dict[str, Any]) -> None:
        self.connection.execute(
            """
            INSERT INTO skills(name, path, description, content_hash, dependencies_json, issues_json, scanned_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                name=excluded.name,
                description=excluded.description,
                content_hash=excluded.content_hash,
                dependencies_json=excluded.dependencies_json,
                issues_json=excluded.issues_json,
                scanned_at=excluded.scanned_at
            """,
            (
                record["name"], record["path"], record["description"], record["content_hash"],
                json.dumps(record["dependencies"]), json.dumps(record["issues"]), utc_now(),
            ),
        )
        self.connection.commit()

    def record_evaluation(self, report: dict[str, Any]) -> None:
        self.connection.execute(
            """
            INSERT INTO evaluations(skill_name, target_path, suite, score, passed, total, results_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report["skill"], report["target"], report["suite"], report["score"],
                report["passed"], report["total"], json.dumps(report["results"]), utc_now(),
            ),
        )
        self.connection.commit()

    def record_candidate(self, record: dict[str, Any]) -> None:
        now = utc_now()
        self.connection.execute(
            """
            INSERT INTO candidates(
                candidate_id, skill_name, baseline_path, candidate_path, baseline_hash,
                candidate_hash, before_score, after_score, holdout_score, status,
                manifest_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["candidate_id"], record["skill_name"], record["baseline_path"],
                record["candidate_path"], record["baseline_hash"], record["candidate_hash"],
                record["before_score"], record["after_score"], record["holdout_score"],
                record["status"], record["manifest_path"], now, now,
            ),
        )
        self.connection.commit()

    def candidate(self, candidate_id: str) -> dict[str, Any]:
        row = self.connection.execute(
            "SELECT * FROM candidates WHERE candidate_id = ?", (candidate_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"Unknown candidate: {candidate_id}")
        return dict(row)

    def update_candidate_status(self, candidate_id: str, status: str) -> None:
        self.connection.execute(
            "UPDATE candidates SET status = ?, updated_at = ? WHERE candidate_id = ?",
            (status, utc_now(), candidate_id),
        )
        self.connection.commit()

    def event(self, event_type: str, skill_name: str | None, details: dict[str, Any]) -> None:
        self.connection.execute(
            "INSERT INTO events(event_type, skill_name, details_json, created_at) VALUES (?, ?, ?, ?)",
            (event_type, skill_name, json.dumps(details), utc_now()),
        )
        self.connection.commit()

    def inventory(self) -> list[dict[str, Any]]:
        rows = self.connection.execute("SELECT * FROM skills ORDER BY name, path").fetchall()
        inventory: list[dict[str, Any]] = []
        for row in rows:
            record = dict(row)
            record["dependencies"] = json.loads(record.pop("dependencies_json"))
            record["issues"] = json.loads(record.pop("issues_json"))
            inventory.append(record)
        return inventory

    def recent_events(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [{**dict(row), "details": json.loads(row["details_json"])} for row in rows]
