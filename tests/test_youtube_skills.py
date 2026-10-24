import copy
import json
import pytest
from vxruntime.youtube_skills import MANIFEST, validate, receipt

def test_registry_receipt():
    r=receipt()
    assert r["skills"]==11 and r["tools"]==6
    assert len(r["manifest_sha256"])==64 and not r["published"]

@pytest.mark.parametrize("change", [
    lambda m: m.update(execution_enabled=True),
    lambda m: m.update(auto_publish=True),
    lambda m: m.update(external_spend_sar=True),
    lambda m: m["skills"].pop(),
    lambda m: m["skills"][0].update(enabled=True),
    lambda m: m["python_tools"][0].update(executable=True),
])
def test_refuses_privilege(change):
    m=json.loads(MANIFEST.read_text(encoding="utf-8"))
    change(m)
    with pytest.raises(ValueError): validate(m)
