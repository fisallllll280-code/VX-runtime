"""Pure, deterministic marketplace sale allocation helpers.

This module performs arithmetic only. It does not accept payments, hold funds,
verify a payment provider, or initiate payouts. All amounts are integer minor
units and a real integration must provide verified settlement evidence.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SaleAllocation:
    currency: str
    gross_minor: int
    commission_bps: int
    platform_commission_minor: int
    processing_fee_minor: int
    tax_minor: int
    reserve_minor: int
    creator_net_minor: int


def allocate_settled_sale(
    *,
    currency: str,
    gross_minor: int,
    commission_bps: int,
    processing_fee_minor: int = 0,
    tax_minor: int = 0,
    reserve_minor: int = 0,
    payment_settled: bool,
) -> SaleAllocation:
    """Calculate a hypothetical settled sale split, or reject unconfirmed funds.

    Commission is rounded half-up to the nearest minor unit. This example
    policy subtracts the commission, processing fee, tax, and reserve from
    gross to derive creator net; a production seller agreement may define a
    different allocation and must version that rule per order.
    """
    if not payment_settled:
        raise ValueError("PAYMENT_NOT_SETTLED")
    if not isinstance(currency, str) or len(currency) != 3 or not currency.isalpha():
        raise ValueError("INVALID_CURRENCY")
    for name, value in (
        ("gross_minor", gross_minor),
        ("commission_bps", commission_bps),
        ("processing_fee_minor", processing_fee_minor),
        ("tax_minor", tax_minor),
        ("reserve_minor", reserve_minor),
    ):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name.upper()}_MUST_BE_INTEGER")
    if gross_minor <= 0:
        raise ValueError("GROSS_MUST_BE_POSITIVE")
    if not 0 <= commission_bps <= 10_000:
        raise ValueError("COMMISSION_BPS_OUT_OF_RANGE")
    if min(processing_fee_minor, tax_minor, reserve_minor) < 0:
        raise ValueError("DEDUCTIONS_MUST_NOT_BE_NEGATIVE")

    # Integer half-up rounding: (gross * bps + 5000) // 10000.
    commission = (gross_minor * commission_bps + 5_000) // 10_000
    deductions = commission + processing_fee_minor + tax_minor + reserve_minor
    if deductions > gross_minor:
        raise ValueError("DEDUCTIONS_EXCEED_GROSS")

    return SaleAllocation(
        currency=currency.upper(),
        gross_minor=gross_minor,
        commission_bps=commission_bps,
        platform_commission_minor=commission,
        processing_fee_minor=processing_fee_minor,
        tax_minor=tax_minor,
        reserve_minor=reserve_minor,
        creator_net_minor=gross_minor - deductions,
    )
