import pytest
from tools.vx_engineering_depth_compiler import compile_depth, DIMENSIONS

SPEC = {"capability_id": "VX.TEST.001", "source": {"repository": "VAIXLNS", "revision": "abc123"}}


def test_incomplete_design_proposes_measurable_gates():
    result = compile_depth(SPEC)
    assert len(result["missing"]) == len(DIMENSIONS)
    assert result["review_state"] == "REQUIRES_INDEPENDENT_VERIFICATION"
    assert not result["execution_authorized"]
    assert not result["canonical_promotion_authorized"]
    assert all(p["state"] == "PROPOSED" and p["evidence"] is None for p in result["engineering_proposals"])


def test_complete_claims_are_not_verified():
    spec = {**SPEC, "assurances": {k: {"reference": "claims.md#section"} for k in DIMENSIONS}}
    result = compile_depth(spec)
    assert result["missing"] == []
    assert result["declaration_coverage"]["declared"] == len(DIMENSIONS)
    assert result["review_state"] != "VERIFIED"
    assert not result["novelty_verified"]


def test_determinism_and_identity():
    assert compile_depth(SPEC) == compile_depth(dict(reversed(list(SPEC.items()))))
    with pytest.raises(ValueError):
        compile_depth({"capability_id": "", "source": SPEC["source"]})
    with pytest.raises(ValueError):
        compile_depth({"capability_id": "x", "source": {}})


def test_unknown_dimensions_and_realms_fail_closed():
    with pytest.raises(ValueError):
        compile_depth({**SPEC, "assurances": {"override_governance": {"reference": "x"}}})
    with pytest.raises(ValueError):
        compile_depth({**SPEC, "claimed_realms": ["all-powerful"]})
