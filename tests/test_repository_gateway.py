from vxruntime.repository_gateway import CAPABILITY, OWNER, ReadGrant, governed_repository_read


def test_allowed_read_has_hash_linked_receipt():
    seen = []
    def fetch(repo):
        seen.append(repo)
        return {"full_name": f"{OWNER}/{repo}", "default_branch": "main"}
    result = governed_repository_read("read-1", ReadGrant("NEXENT", CAPABILITY, True), fetch)
    assert seen == ["NEXENT"]
    assert result["status"] == "success"
    assert result["ledger_valid"] and len(result["event_digest"]) == 64
    assert result["federation_edge_activated"] is False


def test_unapproved_request_does_not_call_fetcher():
    seen = []
    result = governed_repository_read("read-2", ReadGrant("NEXENT", CAPABILITY), lambda r: seen.append(r))
    assert result["status"] == "blocked" and seen == []


def test_unknown_repo_blocked():
    result = governed_repository_read("read-3", ReadGrant("unknown", CAPABILITY, True),
                                      lambda _: (_ for _ in ()).throw(AssertionError("should not fetch")))
    assert result["status"] == "blocked"


def test_identity_mismatch_failed_with_evidence():
    result = governed_repository_read("read-4", ReadGrant("NEXENT", CAPABILITY, True),
                                      lambda _: {"full_name": "wrong/repo", "default_branch": "main"})
    assert result["status"] == "failed"
    assert result["error"] == "REPOSITORY_IDENTITY_MISMATCH"
    assert result["ledger_valid"]


def test_connection_failure_is_not_success():
    def fetch(_):
        raise OSError("offline")
    result = governed_repository_read("read-5", ReadGrant("VAIXLNS", CAPABILITY, True), fetch)
    assert result["status"] == "failed" and result["error"] == "offline"


def test_wrong_capability_blocked():
    result = governed_repository_read("read-6", ReadGrant("NEXENT", "github.write", True), lambda _: None)
    assert result["status"] == "blocked"
