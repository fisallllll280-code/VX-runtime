import pytest

from vxruntime.marketplace_ledger import allocate_settled_sale


def test_settled_sale_allocates_commission_and_net_in_minor_units():
    result = allocate_settled_sale(
        currency="sar",
        gross_minor=10_000,
        commission_bps=1_000,
        processing_fee_minor=250,
        tax_minor=0,
        reserve_minor=500,
        payment_settled=True,
    )
    assert result.currency == "SAR"
    assert result.platform_commission_minor == 1_000
    assert result.creator_net_minor == 8_250


def test_unsettled_payment_cannot_create_creator_earnings():
    with pytest.raises(ValueError, match="PAYMENT_NOT_SETTLED"):
        allocate_settled_sale(
            currency="SAR", gross_minor=10_000, commission_bps=1_000,
            payment_settled=False,
        )


@pytest.mark.parametrize("gross, bps", [(0, 100), (-1, 100), (100, -1), (100, 10_001)])
def test_invalid_gross_or_commission_is_rejected(gross, bps):
    with pytest.raises(ValueError):
        allocate_settled_sale(
            currency="SAR", gross_minor=gross, commission_bps=bps,
            payment_settled=True,
        )


def test_commission_rounds_half_up_without_floating_point():
    result = allocate_settled_sale(
        currency="USD", gross_minor=1, commission_bps=5_000,
        payment_settled=True,
    )
    assert result.platform_commission_minor == 1
    assert result.creator_net_minor == 0


def test_deductions_cannot_exceed_gross():
    with pytest.raises(ValueError, match="DEDUCTIONS_EXCEED_GROSS"):
        allocate_settled_sale(
            currency="SAR", gross_minor=100, commission_bps=1_000,
            processing_fee_minor=100, payment_settled=True,
        )


def test_float_money_amounts_are_rejected():
    with pytest.raises(ValueError, match="GROSS_MINOR_MUST_BE_INTEGER"):
        allocate_settled_sale(
            currency="SAR", gross_minor=1.25, commission_bps=1_000,
            payment_settled=True,
        )
