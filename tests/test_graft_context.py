from pathlib import Path
from subprocess import CompletedProcess
import pytest
from vxruntime.graft_context import plan, execute


def root(tmp_path):
    (tmp_path / ".git").mkdir()
    return tmp_path


def test_allowed_read_commands(tmp_path):
    r = root(tmp_path)
    assert plan("check", str(r))["argv"] == ["check", "--json"]
    assert plan("ask", str(r), "auth flows")["argv"] == ["ask", "auth flows", "--json"]


def test_no_deep_or_init(tmp_path):
    r = root(tmp_path)
    for op in ("init", "install", "build --deep", "mcp"):
        with pytest.raises(ValueError):
            plan(op, str(r))


def test_denied_without_approval(tmp_path):
    p = plan("map", str(root(tmp_path)))
    assert execute(p)["status"] == "BLOCKED"


def test_tampered_flags_denied(tmp_path):
    p = plan("build", str(root(tmp_path)))
    p["argv"].append("--deep")
    assert execute(p, approved=True)["status"] == "BLOCKED"


def test_mock_execution_receipt(tmp_path):
    p = plan("check", str(root(tmp_path)))
    executable = tmp_path / "graft"
    executable.write_text("test")
    calls = []
    def runner(args, **kwargs):
        calls.append((args, kwargs))
        return CompletedProcess(args, 0, '{"fresh":true}', "")
    result = execute(p, approved=True, executable=str(executable), runner=runner)
    assert result["status"] == "SUCCESS"
    assert len(result["output_sha256"]) == 64
    assert calls[0][0][1:] == ["check", "--json"]
    assert calls[0][1]["timeout"] == 45


def test_requires_pinned_binary(tmp_path):
    p = plan("ask", str(root(tmp_path)), "dependency")
    assert execute(p, approved=True, executable="graft")["status"] == "BLOCKED"
