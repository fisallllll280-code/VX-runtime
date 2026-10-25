from tools.vx_depth_source_extractor import extract, build_reviews


def test_source_bound_extraction_and_depth(tmp_path):
    (tmp_path / "index.md").write_text("# Innovation Index\n1. Architecture Self-Discovery Engine\n2. Capability Genome\n", encoding="utf-8")
    r = extract(tmp_path, "VAIXLNS", "pinnedSHA")
    assert r["record_count"] == 3
    assert r["errors"] == []
    assert r["records"][1]["title"] == "Architecture Self-Discovery Engine"
    assert len(r["records"][1]["source"]["sha256"]) == 64
    reviews = build_reviews(r)
    assert len(reviews) == 3
    assert reviews[1]["review_state"] == "REQUIRES_INDEPENDENT_VERIFICATION"
    assert not reviews[1]["execution_authorized"]


def test_extraction_deterministic_and_excludes_generated(tmp_path):
    (tmp_path / "a.md").write_text("# Provenance Ledger", encoding="utf-8")
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "b.md").write_text("# NotIndexed", encoding="utf-8")
    assert extract(tmp_path, "VAIXLNS", "sha") == extract(tmp_path, "VAIXLNS", "sha")
    assert extract(tmp_path, "VAIXLNS", "sha")["record_count"] == 1


def test_missing_source_fails_closed(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        extract(tmp_path / "missing", "VAIXLNS", "sha")
