"""Configurable marketplace policy defaults; no live payment movement.

These values are implementation defaults, not a claim that the marketplace or payouts
are live. Market availability and creator eligibility must be explicitly verified.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .marketplace_ledger import SaleAllocation, allocate_settled_sale

ProductType = Literal["apps", "agents", "tools", "apis", "workflows"]
SUPPORTED_PRODUCT_TYPES = frozenset({"apps", "agents", "tools", "apis", "workflows"})


@dataclass(frozen=True)
class MarketplacePolicy:
    standard_commission_bps: int = 1_000
    creator_launch_commission_bps: int = 500
    payout_cadence: str = "WEEKLY_AFTER_SETTLEMENT_AND_VERIFICATION"
    launch_country: str = "SA"
    global_expansion_mode: str = "PER_MARKET_REVIEW_REQUIRED"
    supported_product_types: frozenset[str] = SUPPORTED_PRODUCT_TYPES

    def __post_init__(self) -> None:
        for name, value in (
            ("standard_commission_bps", self.standard_commission_bps),
            ("creator_launch_commission_bps", self.creator_launch_commission_bps),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 10_000:
                raise ValueError(f"{name.upper()}_OUT_OF_RANGE")
        if not isinstance(self.launch_country, str) or len(self.launch_country) != 2:
            raise ValueError("INVALID_LAUNCH_COUNTRY")
        if not self.supported_product_types or not self.supported_product_types.issubset(SUPPORTED_PRODUCT_TYPES):
            raise ValueError("UNSUPPORTED_PRODUCT_TYPE_POLICY")

    def commission_bps_for(self, *, creator_launch_eligible: bool) -> int:
        if not isinstance(creator_launch_eligible, bool):
            raise ValueError("CREATOR_LAUNCH_ELIGIBILITY_MUST_BE_EXPLICIT")
        return (
            self.creator_launch_commission_bps
            if creator_launch_eligible
            else self.standard_commission_bps
        )

    def supports_product_type(self, product_type: str) -> bool:
        return isinstance(product_type, str) and product_type.strip().lower() in self.supported_product_types

    def payout_block_reason(
        self,
        *,
        provider_settled: bool,
        creator_verified: bool,
        payout_destination_verified: bool,
        compliance_cleared: bool,
        available_minor: int,
        requested_minor: int,
    ) -> str | None:
        """Return a fail-closed reason; this does not schedule or send a payout."""
        if not provider_settled:
            return "PROVIDER_SETTLEMENT_REQUIRED"
        if not creator_verified:
            return "CREATOR_VERIFICATION_REQUIRED"
        if not payout_destination_verified:
            return "PAYOUT_DESTINATION_VERIFICATION_REQUIRED"
        if not compliance_cleared:
            return "COMPLIANCE_CLEARANCE_REQUIRED"
        if any(isinstance(v, bool) or not isinstance(v, int) for v in (available_minor, requested_minor)):
            return "AMOUNTS_MUST_BE_INTEGER_MINOR_UNITS"
        if requested_minor <= 0:
            return "PAYOUT_AMOUNT_MUST_BE_POSITIVE"
        if available_minor < 0 or requested_minor > available_minor:
            return "INSUFFICIENT_AVAILABLE_BALANCE"
        return None


def allocate_creator_sale(
    *,
    policy: MarketplacePolicy,
    creator_launch_eligible: bool,
    currency: str,
    gross_minor: int,
    payment_settled: bool,
    processing_fee_minor: int = 0,
    tax_minor: int = 0,
    reserve_minor: int = 0,
) -> SaleAllocation:
    """Apply configured commission policy to the existing pure allocation helper."""
    return allocate_settled_sale(
        currency=currency,
        gross_minor=gross_minor,
        commission_bps=policy.commission_bps_for(
            creator_launch_eligible=creator_launch_eligible
        ),
        processing_fee_minor=processing_fee_minor,
        tax_minor=tax_minor,
        reserve_minor=reserve_minor,
        payment_settled=payment_settled,
    )
