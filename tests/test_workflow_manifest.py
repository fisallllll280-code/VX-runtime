import json

from vxruntime.workflow_manifest import parse_workflow_json, validate_workflow


def valid_manifest():
    return {
        "workflow_id": "build.app",
        "version": "1.0",
        "tasks": [
            {
                "task_id": "test",
                "capability": "test.run",
                "operation": "pytest",
                "depends_on": ["build"],
                "inputs": {"suite": "unit"},
                "timeout_seconds": 30,
                "side_effects": ["none"],
            },
            {
                "task_id": "build",
                "capability": "build.run",
                "operation": "compile",
                "depends_on": [],
                "inputs": {"target": "python"},
                "timeout_seconds": 60,
                "side_effects": ["none"],
            },
        ],
    }


def test_valid_manifest_normalizes_deterministically():
    first = validate_workflow(valid_manifest(), registered_capabilities={"test.run", "build.run"})
    second = validate_workflow(valid_manifest(), registered_capabilities={"test.run", "build.run"})
    assert first.valid
    assert first.errors == ()
    assert first.normalized == second.normalized
    assert [task["task_id"] for task in first.normalized["tasks"]] == ["build", "test"]


def test_unknown_capability_fails_closed_when_allowlist_is_given():
    result = validate_workflow(valid_manifest(), registered_capabilities={"build.run"})
    assert not result.valid
    assert "UNREGISTERED_CAPABILITY:test.run" in result.errors


def test_unknown_fields_and_versions_are_rejected():
    manifest = valid_manifest()
    manifest["untrusted"] = True
    manifest["version"] = "9.9"
    result = validate_workflow(manifest)
    assert not result.valid
    assert "UNKNOWN_ROOT_FIELD:untrusted" in result.errors
    assert "UNSUPPORTED_WORKFLOW_VERSION:'9.9'" in result.errors


def test_duplicate_task_ids_and_unknown_dependencies_are_rejected():
    manifest = valid_manifest()
    manifest["tasks"][1]["task_id"] = "test"
    result = validate_workflow(manifest)
    assert not result.valid
    assert "DUPLICATE_TASK_ID:test" in result.errors
    assert any(error.startswith("UNKNOWN_DEPENDENCY:") for error in result.errors)


def test_cycles_are_rejected():
    manifest = valid_manifest()
    manifest["tasks"][1]["depends_on"] = ["test"]
    result = validate_workflow(manifest)
    assert not result.valid
    assert any(error.startswith("DEPENDENCY_CYCLE:") for error in result.errors)


def test_invalid_timeout_side_effect_and_dependency_are_rejected():
    manifest = valid_manifest()
    manifest["tasks"][0]["timeout_seconds"] = 0
    manifest["tasks"][0]["side_effects"] = ["execute_everything"]
    manifest["tasks"][0]["depends_on"] = ["missing"]
    result = validate_workflow(manifest)
    assert not result.valid
    assert "TASK[0]:TIMEOUT_MUST_BE_POSITIVE_NUMBER" in result.errors
    assert "TASK[0]:INVALID_SIDE_EFFECTS" in result.errors
    assert "UNKNOWN_DEPENDENCY:test:missing" in result.errors


def test_json_parser_returns_stable_invalid_json_error():
    result = parse_workflow_json("{")
    assert not result.valid
    assert result.errors == ("INVALID_JSON",)


def test_non_object_root_is_rejected():
    result = validate_workflow(["not", "an", "object"])
    assert not result.valid
    assert result.errors == ("ROOT_MUST_BE_OBJECT",)
