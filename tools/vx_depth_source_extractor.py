"""Read-only source-bound extraction feeding VX Engineering Depth Compiler."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from tools.vx_engineering_depth_compiler import compile_depth

HEAD = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$")
NUMBERED = re.compile(r"^\s*(\d{1,4})[.)]\s+(.+?)\s*$")
EXTS = {".md", ".json"}
SKIP = {".git", "build", "__pycache__", "node_modules", ".venv"}
MAX_BYTES = 2_000_000


def extract(root: Path, repository: str, revision: str) -> dict:
    if not root.is_dir() or not repository or not revision:
        raise ValueError("A readable root, repository and pinned revision are required")
    records = []
    errors = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if not path.is_file() or path.suffix.lower() not in EXTS or any(x in SKIP for x in rel.parts):
            continue
        try:
            if path.stat().st_size > MAX_BYTES:
                errors.append({"path": rel.as_posix(), "reason": "OVERSIZE"})
                continue
            raw = path.read_bytes()
            lines = raw.decode("utf-8").splitlines()
        except (OSError, UnicodeError):
            errors.append({"path": rel.as_posix(), "reason": "UNREADABLE"})
            continue
        digest = hashlib.sha256(raw).hexdigest()
        for n, line in enumerate(lines, 1):
            match = HEAD.match(line) or NUMBERED.match(line)
            if not match:
                continue
            title = match.group(match.lastindex).strip()
            if len(title) < 4:
                continue
            identity = hashlib.sha256(f"{repository}:{revision}:{rel}:{n}:{title}".encode()).hexdigest()[:20]
            records.append({"record_id": identity, "title": title,
                            "source": {"repository": repository, "revision": revision,
                                       "path": rel.as_posix(), "line": n, "sha256": digest},
                            "state": "EXTRACTED_UNVERIFIED"})
    return {"schema": "vx.depth.extraction.v1", "records": records,
            "errors": errors, "record_count": len(records)}


def build_reviews(extraction: dict) -> list[dict]:
    reviews = []
    for record in extraction["records"]:
        spec = {"capability_id": record["record_id"],
                "source": record["source"], "assurances": {}}
        review = compile_depth(spec)
        review["title"] = record["title"]
        reviews.append(review)
    return reviews


def main() -> int:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--revision", required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = extract(args.root, args.repo, args.revision)
    result["reviews"] = build_reviews(result)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 2 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
