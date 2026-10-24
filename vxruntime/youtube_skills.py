"""Fail-closed, pinned YouTube skill catalog. Never runs third-party scripts."""
import hashlib
import json
from pathlib import Path

MANIFEST = Path(__file__).resolve().parents[1] / "registry" / "youtube_skills.v1.json"
NAMES = frozenset(["yt-audit","yt-chapters","yt-comment","yt-edit","yt-package","yt-plan","yt-retention","yt-script","yt-seo","yt-shorts","yt-viral"])

def validate(m):
    if not isinstance(m, dict) or m.get("schema_version") != "1.0.0":
        raise ValueError("BAD_SCHEMA")
    if m.get("execution_enabled") is not False or m.get("auto_publish") is not False:
        raise ValueError("PRIVILEGED_MODE")
    if type(m.get("external_spend_sar")) is not int or m["external_spend_sar"] != 0:
        raise ValueError("UNAPPROVED_SPEND")
    skills = m.get("skills")
    if not isinstance(skills, list) or len(skills) != 11 or {x.get("id") for x in skills if isinstance(x, dict)} != NAMES:
        raise ValueError("INVALID_SKILLS")
    if any(x.get("enabled") is not False or x.get("source") != f"skills/{x['id']}/SKILL.md" for x in skills):
        raise ValueError("ACTIVE_SKILL")
    utilities = m.get("python_tools")
    if not isinstance(utilities, list) or len(utilities) != 6 or any(
        not isinstance(x, dict) or x.get("executable") is not False or
        not isinstance(x.get("git_blob_sha"), str) or len(x["git_blob_sha"]) != 40
        for x in utilities):
        raise ValueError("UNSAFE_UTILITIES")
    return m

def receipt():
    m = validate(json.loads(MANIFEST.read_text(encoding="utf-8")))
    digest = hashlib.sha256(json.dumps(m, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"status":"REGISTERED_NOT_INSTALLED","manifest_sha256":digest,
            "skills":11,"tools":6,"external_spend_sar":0,"published":False}
