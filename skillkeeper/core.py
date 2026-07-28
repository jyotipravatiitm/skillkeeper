from __future__ import annotations

import difflib
import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .store import Store


FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", re.DOTALL)
DEPENDENCY = re.compile(r"\$([a-z0-9][a-z0-9-]{0,63})")
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = FRONTMATTER.match(text)
    if not match:
        return {}, text
    fields: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        if ":" not in raw_line or raw_line.startswith((" ", "\t")):
            continue
        key, value = raw_line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"\'')
    return fields, match.group(2)


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    path: Path
    text: str
    body: str
    dependencies: tuple[str, ...]
    issues: tuple[str, ...]

    @property
    def hash(self) -> str:
        return content_hash(self.text)


def load_skill(path: Path) -> Skill:
    skill_file = path if path.name == "SKILL.md" else path / "SKILL.md"
    if not skill_file.exists():
        raise ValueError(f"No SKILL.md at {skill_file}")
    text = skill_file.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(text)
    issues: list[str] = []
    name = fields.get("name", "")
    description = fields.get("description", "")
    if not name:
        issues.append("missing-name")
    elif not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", name):
        issues.append("invalid-name")
    if not description:
        issues.append("missing-description")
    extra = sorted(set(fields) - {"name", "description"})
    if extra:
        issues.append("extra-frontmatter:" + ",".join(extra))
    for link in MARKDOWN_LINK.findall(body):
        if "://" in link or link.startswith("#"):
            continue
        target = (skill_file.parent / link.split("#", 1)[0]).resolve()
        if not target.exists():
            issues.append(f"missing-reference:{link}")
    return Skill(
        name=name or skill_file.parent.name,
        description=description,
        path=skill_file.parent.resolve(),
        text=text,
        body=body,
        dependencies=tuple(sorted(set(DEPENDENCY.findall(body)))),
        issues=tuple(issues),
    )


def scan(roots: Iterable[Path], store: Store) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for root in roots:
        for skill_file in sorted(root.resolve().glob("*/SKILL.md")):
            skill = load_skill(skill_file)
            record = {
                "name": skill.name,
                "path": str(skill.path),
                "description": skill.description,
                "content_hash": skill.hash,
                "dependencies": list(skill.dependencies),
                "issues": list(skill.issues),
            }
            store.upsert_skill(record)
            records.append(record)
    names = {record["name"] for record in records}
    for record in records:
        unresolved = sorted(set(record["dependencies"]) - names)
        if unresolved:
            record["issues"].extend(f"unresolved-skill:{name}" for name in unresolved)
            store.upsert_skill(record)
    store.event("inventory.scanned", None, {"roots": [str(p.resolve()) for p in roots], "count": len(records)})
    return records


def load_cases(paths: Iterable[Path]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for path in paths:
        candidates = sorted(path.glob("*.json")) if path.is_dir() else [path]
        for candidate in candidates:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
            payload["_path"] = str(candidate.resolve())
            cases.append(payload)
    return cases


def evaluate(skill_path: Path, cases: list[dict[str, Any]], suite: str = "replay") -> dict[str, Any]:
    skill = load_skill(skill_path)
    haystack = re.sub(r"\s+", " ", skill.body.lower())
    results: list[dict[str, Any]] = []
    passed = 0
    total = 0
    for case in cases:
        if case.get("skill") not in (None, skill.name):
            continue
        checks: list[dict[str, Any]] = []
        for requirement in case.get("requirements", []):
            signals = [signal.lower() for signal in requirement.get("signals", [])]
            mode = requirement.get("mode", "all")
            matches = [signal in haystack for signal in signals]
            ok = bool(matches) and (all(matches) if mode == "all" else any(matches))
            checks.append(
                {
                    "id": requirement["id"],
                    "passed": ok,
                    "description": requirement.get("description", requirement["id"]),
                    "missing_signals": [signal for signal, match in zip(signals, matches) if not match],
                    "repair": requirement.get("repair", ""),
                }
            )
            total += 1
            passed += int(ok)
        results.append({"case": case["id"], "prompt": case.get("prompt", ""), "checks": checks})
    score = round(passed / total, 3) if total else 0.0
    return {
        "skill": skill.name,
        "target": str(skill.path),
        "suite": suite,
        "score": score,
        "passed": passed,
        "total": total,
        "results": results,
    }


def failed_repairs(report: dict[str, Any]) -> list[str]:
    repairs: list[str] = []
    for case in report["results"]:
        for check in case["checks"]:
            repair = check.get("repair", "").strip()
            if not check["passed"] and repair and repair not in repairs:
                repairs.append(repair)
    return repairs


def make_candidate_text(skill: Skill, repairs: list[str], max_repairs: int = 12) -> str:
    bounded = repairs[:max_repairs]
    if not bounded:
        return skill.text
    block = [
        "",
        "## Quality contract",
        "",
        "Apply these requirements to every presentation unless the user explicitly overrides one:",
        "",
        *[f"- {repair}" for repair in bounded],
        "",
        "Before handoff, verify each requirement against the generated presentation and report any exception.",
    ]
    return skill.text.rstrip() + "\n" + "\n".join(block) + "\n"


def heal(
    skill_path: Path,
    train_cases: list[dict[str, Any]],
    holdout_cases: list[dict[str, Any]],
    store: Store,
    minimum_train: float = 1.0,
    minimum_holdout: float = 0.8,
    max_repairs: int = 12,
) -> dict[str, Any]:
    skill = load_skill(skill_path)
    before = evaluate(skill.path, train_cases, "train-before")
    repairs = failed_repairs(before)
    candidate_text = make_candidate_text(skill, repairs, max_repairs=max_repairs)
    candidate_hash = content_hash(candidate_text)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    candidate_id = f"{skill.name}-{stamp}-{candidate_hash[:6]}"
    candidate_dir = store.state_dir / "staging" / candidate_id / skill.name
    shutil.copytree(skill.path, candidate_dir)
    (candidate_dir / "SKILL.md").write_text(candidate_text, encoding="utf-8")
    after = evaluate(candidate_dir, train_cases, "train-after")
    holdout = evaluate(candidate_dir, holdout_cases, "holdout")
    improved = after["score"] > before["score"]
    train_ok = bool(after["total"]) and after["score"] >= minimum_train
    holdout_ok = bool(holdout["total"]) and holdout["score"] >= minimum_holdout
    status = "staged" if improved and train_ok and holdout_ok and not load_skill(candidate_dir).issues else "rejected"
    manifest = {
        "candidate_id": candidate_id,
        "skill_name": skill.name,
        "baseline_path": str(skill.path),
        "candidate_path": str(candidate_dir),
        "baseline_hash": skill.hash,
        "candidate_hash": candidate_hash,
        "before_score": before["score"],
        "after_score": after["score"],
        "holdout_score": holdout["score"],
        "minimum_train": minimum_train,
        "minimum_holdout": minimum_holdout,
        "repairs": repairs[:max_repairs],
        "status": status,
    }
    manifest_path = candidate_dir.parent / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    store.record_evaluation(before)
    store.record_evaluation(after)
    store.record_evaluation(holdout)
    store.record_candidate({**manifest, "manifest_path": str(manifest_path)})
    store.event("candidate.created", skill.name, manifest)
    return manifest


def candidate_diff(store: Store, candidate_id: str) -> str:
    candidate = store.candidate(candidate_id)
    before = (Path(candidate["baseline_path"]) / "SKILL.md").read_text(encoding="utf-8").splitlines()
    after = (Path(candidate["candidate_path"]) / "SKILL.md").read_text(encoding="utf-8").splitlines()
    return "\n".join(
        difflib.unified_diff(before, after, fromfile="live/SKILL.md", tofile="candidate/SKILL.md", lineterm="")
    )


def promote(store: Store, candidate_id: str) -> dict[str, Any]:
    candidate = store.candidate(candidate_id)
    if candidate["status"] != "staged":
        raise ValueError(f"Candidate {candidate_id} is {candidate['status']}, not staged")
    live_dir = Path(candidate["baseline_path"])
    current = load_skill(live_dir)
    if current.hash != candidate["baseline_hash"]:
        raise ValueError("Live skill changed after staging; create a fresh candidate")
    source_dir = Path(candidate["candidate_path"])
    staged = load_skill(source_dir)
    if staged.hash != candidate["candidate_hash"]:
        raise ValueError("Staged candidate changed after evaluation; create a fresh candidate")
    backup_dir = store.state_dir / "versions" / current.name / f"{current.hash}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    shutil.copytree(live_dir, backup_dir)
    shutil.copy2(source_dir / "SKILL.md", live_dir / "SKILL.md")
    store.update_candidate_status(candidate_id, "promoted")
    details = {"candidate_id": candidate_id, "backup_path": str(backup_dir), "new_hash": load_skill(live_dir).hash}
    store.event("candidate.promoted", current.name, details)
    return details


def rollback(store: Store, skill_path: Path, backup_path: Path) -> dict[str, Any]:
    live = load_skill(skill_path)
    backup = load_skill(backup_path)
    if live.name != backup.name:
        raise ValueError(f"Backup is for {backup.name}, not {live.name}")
    shutil.copy2(backup.path / "SKILL.md", live.path / "SKILL.md")
    details = {"skill": live.name, "restored_hash": load_skill(live.path).hash, "backup_path": str(backup.path)}
    store.event("skill.rolled_back", live.name, details)
    return details


def health(skill_path: Path, cases: list[dict[str, Any]]) -> dict[str, Any]:
    skill = load_skill(skill_path)
    replay = evaluate(skill.path, cases, "health")
    spec_score = 1.0 if not skill.issues else max(0.0, 1 - 0.25 * len(skill.issues))
    coverage_score = 1.0 if replay["total"] else 0.0
    overall = round(100 * (0.25 * spec_score + 0.25 * coverage_score + 0.5 * replay["score"]), 1)
    state = "healthy" if overall >= 85 else "needs-attention" if overall >= 60 else "unhealthy"
    return {
        "skill": skill.name,
        "path": str(skill.path),
        "health": overall,
        "state": state,
        "spec_score": spec_score,
        "coverage_score": coverage_score,
        "replay_score": replay["score"],
        "passed": replay["passed"],
        "total": replay["total"],
        "issues": list(skill.issues),
    }
