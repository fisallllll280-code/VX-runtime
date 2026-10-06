"""Universal external integration runtime gate for VX."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class IntegrationKind(str, Enum):
    MODEL="MODEL"; API="API"; SERVER="SERVER"; TOOL="TOOL"
    CONNECTOR="CONNECTOR"; REPOSITORY="REPOSITORY"; DATA_SOURCE="DATA_SOURCE"

@dataclass(frozen=True)
class ExternalIntegration:
    integration_id:str
    kind:IntegrationKind
    endpoint:str
    capability:str
    allowed_capabilities:tuple[str,...]
    contract_version:str
    dependency_fingerprint:str
    environment_fingerprint:str
    proof_identity:str
    proof_dependency_fingerprint:str
    proof_environment_fingerprint:str
    proof_expires_epoch:int
    now_epoch:int
    explicit_authority:bool

class ExternalIntegrationGate:
    def authorize(self, x:ExternalIntegration)->bool:
        checks=(
            x.explicit_authority,
            bool(x.integration_id),
            x.capability in x.allowed_capabilities,
            bool(x.endpoint),
            bool(x.contract_version),
            bool(x.dependency_fingerprint),
            bool(x.environment_fingerprint),
            x.proof_identity==x.integration_id,
            x.proof_dependency_fingerprint==x.dependency_fingerprint,
            x.proof_environment_fingerprint==x.environment_fingerprint,
            x.now_epoch < x.proof_expires_epoch,
        )
        return all(checks)

__all__=["IntegrationKind","ExternalIntegration","ExternalIntegrationGate"]
