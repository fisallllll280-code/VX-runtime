"""VX Social Command: local, fail-closed campaign ledger (stdlib only).

No social posting transport is implemented. Approval is a separate explicit act.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

PLATFORMS = ("instagram", "x", "linkedin", "youtube", "tiktok", "facebook",
             "threads", "telegram", "google_business", "pinterest",
             "bluesky", "mastodon", "discord")
STATES = ("DRAFT", "REVIEW", "APPROVED", "REJECTED")
DEFAULT = {"schema": 1, "brand": "VAIXLNS", "accounts": [], "posts": [], "events": []}


class PolicyError(ValueError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def load(path: Path):
    if not path.exists():
        return json.loads(json.dumps(DEFAULT))
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != 1 or not all(k in data for k in ("accounts", "posts", "events")):
        raise PolicyError("Unsupported ledger schema")
    return data


def save(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def event(data, action, actor, subject):
    previous = data["events"][-1]["hash"] if data["events"] else "GENESIS"
    record = {"seq": len(data["events"]) + 1, "time": now(), "action": action,
              "actor": actor, "subject": subject, "previous": previous}
    record["hash"] = digest(record)
    data["events"].append(record)


def validate_actor(actor):
    if not isinstance(actor, str) or not re.fullmatch(r"[A-Za-z0-9_.@-]{2,100}", actor):
        raise PolicyError("Actor identity is required")
    return actor


def register(data, platform, handle, actor):
    validate_actor(actor)
    if platform not in PLATFORMS:
        raise PolicyError("Unknown platform")
    if not re.fullmatch(r"@[A-Za-z0-9_.-]{2,64}", handle):
        raise PolicyError("Invalid handle")
    key = platform + ":" + handle.lower()
    if any(a["id"] == key for a in data["accounts"]):
        raise PolicyError("Duplicate account")
    data["accounts"].append({"id": key, "platform": platform, "handle": handle,
                             "status": "UNCONNECTED", "external_id": None})
    event(data, "ACCOUNT_REGISTERED", actor, key)
    return key


def draft(data, account_id, body, actor):
    validate_actor(actor)
    if not any(a["id"] == account_id for a in data["accounts"]):
        raise PolicyError("Unregistered account")
    if not isinstance(body, str) or not body.strip() or len(body) > 5000:
        raise PolicyError("Invalid message")
    post_id = "POST-" + str(len(data["posts"]) + 1).zfill(6)
    data["posts"].append({"id": post_id, "account": account_id, "body": body,
                          "author": actor, "state": "DRAFT", "reviewer": None,
                          "approval_hash": None, "delivery": "DISABLED"})
    event(data, "DRAFT_CREATED", actor, post_id)
    return post_id


def transition(data, post_id, decision, actor):
    validate_actor(actor)
    matches = [p for p in data["posts"] if p["id"] == post_id]
    if not matches:
        raise PolicyError("Unknown post")
    p = matches[0]
    if decision == "submit" and p["state"] == "DRAFT":
        p["state"] = "REVIEW"
    elif decision in ("approve", "reject") and p["state"] == "REVIEW":
        if p["author"] == actor:
            raise PolicyError("Author cannot self-approve/reject")
        p["state"] = "APPROVED" if decision == "approve" else "REJECTED"
        p["reviewer"] = actor
        p["approval_hash"] = digest({"id": post_id, "body": p["body"], "account": p["account"]}) if decision == "approve" else None
    else:
        raise PolicyError("Invalid state transition")
    event(data, decision.upper(), actor, post_id)
    return p["state"]


def publish(data, post_id, actor):
    # Deliberately impossible: require a separately implemented and proven live
    # adapter, credential vault, connected identity and owner release authorization.
    raise PolicyError("PUBLISH_DISABLED: no verified transport, account connection or release permission")


def verify(data):
    prev = "GENESIS"
    for idx, record in enumerate(data["events"], 1):
        claim = {k: v for k, v in record.items() if k != "hash"}
        if record["seq"] != idx or record["previous"] != prev or record["hash"] != digest(claim):
            raise PolicyError("Audit chain integrity failure")
        prev = record["hash"]
    return {"events": len(data["events"]), "chain_sha256": prev, "accounts": len(data["accounts"]),
            "posts": len(data["posts"]), "connected": 0, "published": 0,
            "live_transport": "DISABLED"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=Path("build/social-command/ledger.json"))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    a = sub.add_parser("register"); a.add_argument("platform"); a.add_argument("handle"); a.add_argument("--actor", required=True)
    a = sub.add_parser("draft"); a.add_argument("account"); a.add_argument("body"); a.add_argument("--actor", required=True)
    a = sub.add_parser("transition"); a.add_argument("post"); a.add_argument("decision", choices=("submit", "approve", "reject")); a.add_argument("--actor", required=True)
    a = sub.add_parser("publish"); a.add_argument("post"); a.add_argument("--actor", required=True)
    args = parser.parse_args(argv)
    try:
        data = load(args.ledger)
        if args.command == "status":
            result = verify(data)
        elif args.command == "register":
            result = {"account": register(data, args.platform, args.handle, args.actor)}
        elif args.command == "draft":
            result = {"post": draft(data, args.account, args.body, args.actor)}
        elif args.command == "transition":
            result = {"state": transition(data, args.post, args.decision, args.actor)}
        else:
            publish(data, args.post, args.actor)
        if args.command != "status":
            save(args.ledger, data)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (PolicyError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
