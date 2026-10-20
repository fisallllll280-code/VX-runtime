"""Read-only VX federation index discovery. Never promotes source claims to authority."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

FAMILIES = ("VA", "NX", "XN", "NA", "AN", "XV", "V", "VV", "VX", "NEXNET", "NEXENT", "VLNS", "AX", "XA", "AV", "VN", "NV")
SUFFIXES = {".md", ".json", ".jsonl", ".yaml", ".yml", ".py", ".toml", ".txt"}
EXCLUDE = {".git", ".venv", "node_modules", "build", "dist", "__pycache__", ".pytest_cache"}
MAX_BYTES = 2_000_000


def discover(roots: dict[str, str]) -> dict:
    """Index exact acronym mentions in accessible local roots, without guessing system identity."""
    result = {"schema": "vx.federation.discovery.v1", "state": "SOURCE_OBSERVED_ONLY",
              "families": {family: [] for family in FAMILIES}, "sources": [], "errors": []}
    for repo, location in sorted(roots.items()):
        root = Path(location).resolve()
        if not root.is_dir():
            result["errors"].append({"repo": repo, "reason": "INACCESSIBLE"})
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in SUFFIXES or any(p in EXCLUDE for p in path.relative_to(root).parts):
                continue
            try:
                if path.stat().st_size > MAX_BYTES:
                    continue
                raw = path.read_bytes()
                content = raw.decode("utf-8")
            except (OSError, UnicodeError):
                continue
            ref = {"repository": repo, "path": path.relative_to(root).as_posix(),
                   "sha256": hashlib.sha256(raw).hexdigest()}
            matches = [f for f in FAMILIES if re.search(r"(?<![A-Za-z0-9_])" + re.escape(f) + r"(?![A-Za-z0-9_])", content)]
            if matches:
                result["sources"].append(ref)
                for f in matches:
                    result["families"][f].append(ref)
    result["counts"] = {f: len(v) for f, v in result["families"].items()}
    return result


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", action="append", required=True, help="repo=/checked/out/path")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    roots = {}
    for s in args.source:
        if "=" not in s:
            parser.error("expected repo=path")
        k, v = s.split("=", 1)
        if not k or not v or k in roots:
            parser.error("duplicate or empty source")
        roots[k] = v
    report = discover(roots)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if not report["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
