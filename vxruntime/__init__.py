"""Minimal deterministic VX runtime reference implementation."""
from .core import Execution,ExecutionPolicy,ExecutionStatus,Event,EventLedger,VXRuntime,canonical_json,digest
from .external_integration import ExternalIntegration,ExternalIntegrationGate,IntegrationKind
from .apple_device import AppleDeviceAdapter, DetectionStatus, DeviceMode, DiscoveryReport
from .apple_capabilities import (
    DISCOVER_CAPABILITY, PREPARE_UPDATE_CAPABILITY,
    execute_discovery, execute_update_preparation,
)
__all__=[
    "Execution","ExecutionPolicy","ExecutionStatus","Event","EventLedger","VXRuntime","canonical_json","digest",
    "ExternalIntegration","ExternalIntegrationGate","IntegrationKind",
    "AppleDeviceAdapter","DetectionStatus","DeviceMode","DiscoveryReport",
    "DISCOVER_CAPABILITY","PREPARE_UPDATE_CAPABILITY","execute_discovery","execute_update_preparation",
]
