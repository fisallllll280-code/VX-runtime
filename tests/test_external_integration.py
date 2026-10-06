from vxruntime.external_integration import ExternalIntegration, ExternalIntegrationGate, IntegrationKind

def base(**changes):
    v=dict(
        integration_id="model:runtime", kind=IntegrationKind.MODEL, endpoint="provider://model",
        capability="inference", allowed_capabilities=("inference",), contract_version="v1",
        dependency_fingerprint="dep:v1", environment_fingerprint="env:v1",
        proof_identity="model:runtime", proof_dependency_fingerprint="dep:v1",
        proof_environment_fingerprint="env:v1", proof_expires_epoch=200, now_epoch=120,
        explicit_authority=True)
    v.update(changes)
    return ExternalIntegration(**v)

def test_external_integration_must_be_proven_and_authorized():
    assert ExternalIntegrationGate().authorize(base())

def test_drift_or_expiry_blocks():
    g=ExternalIntegrationGate()
    assert not g.authorize(base(proof_dependency_fingerprint="dep:v2"))
    assert not g.authorize(base(now_epoch=200))

def test_capability_escalation_blocks():
    assert not ExternalIntegrationGate().authorize(base(capability="filesystem_write"))
