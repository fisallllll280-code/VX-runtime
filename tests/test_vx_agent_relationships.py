from tools.vx_agent_relationships import analyze

def test_overlap_is_not_merge():
    data={"sources":[{"repository":"r","group":"g","path":"agents.json","entries":[{"name":"Architecture Auditor"},{"name":"Architecture Reviewer"},{"name":"Physics Specialist"}]}]}
    result=analyze(data)
    assert result["entries"]==3
    assert len(result["candidate_links"])>=1
    assert all(x["relation"]=="OVERLAP_CANDIDATE_NOT_IDENTITY" for x in result["candidate_links"])
    assert result["identity_merges"]==0
    assert result["authorized_runtime_agents"]==0

def test_fail_closed():
    import pytest
    with pytest.raises(ValueError):
        analyze({})
    with pytest.raises(ValueError):
        analyze({"sources":[{"repository":"x","group":"y","path":"z","entries":[{"name":""}]}]})
