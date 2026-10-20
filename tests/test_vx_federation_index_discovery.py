import json
from pathlib import Path
from tools.vx_federation_index_discovery import discover


def test_exact_family_matches_and_provenance(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "a.md").write_text("VA NX XN NA AN XV VX NEXNET", encoding="utf-8")
    (root / "b.md").write_text("NAVAL ANOTHER XNV", encoding="utf-8")
    report = discover({"example": str(root)})
    for family in ("VA", "NX", "XN", "NA", "AN", "XV", "VX", "NEXNET"):
        assert report["counts"][family] == 1
        assert len(report["families"][family][0]["sha256"]) == 64
    assert report["state"] == "SOURCE_OBSERVED_ONLY"


def test_inaccessible_fails_closed(tmp_path):
    report = discover({"missing": str(tmp_path / "none")})
    assert report["errors"][0]["reason"] == "INACCESSIBLE"
    assert all(v == 0 for v in report["counts"].values())


def test_ignores_generated_and_binary(tmp_path):
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "x.md").write_text("XV", encoding="utf-8")
    (tmp_path / "z.png").write_bytes(b"XV")
    assert discover({"repo": str(tmp_path)})["counts"]["XV"] == 0
