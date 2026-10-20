import pytest

from vxruntime.marketplace_policy import MarketplacePolicy, allocate_creator_sale


def test_default_policy_matches_approved_marketplace_settings():
    policy = MarketplacePolicy()
    assert policy.standard_commission_bps == 1_000
    assert policy.creator_launch_commission_bps == 500
    assert policy.payout_cadence == "WEEKLY_AFTER_SETTLEMENT_AND_VERIFICATION"
    assert policy.launch_country == "SA"
    assert policy.global_expansion_mode == "PER_MARKET_REVIEW_REQUIRED"
    assert policy.supported_product_types == {"apps", "agents", "tools", "apis", "workflows"}


@pytest.mark.parametrize(
    ("eligible", "expected_commission", "expected_creator_net"),
    [(False, 1_000, 9_000), (True, 500, 9_500)],
)
def test_policy_commission_is_integrated_with_settled_sale(
    eligible, expected_commission, expected_creator_net
):
    result = allocate_creator_sale(
        policy=MarketplacePolicy(),
        creator_launch_eligible=eligible,
        currency="SAR",
        gross_minor=10_000,
        payment_settled=True,
    )
    assert result.platform_commission_minor == expected_commission
    assert result.creator_net_minor == expected_creator_net


def test_launch_eligibility_must_be_explicit():
    with pytest.raises(ValueError, match="CREATOR_LAUNCH_ELIGIBILITY_MUST_BE_EXPLICIT"):
        MarketplacePolicy().commission_bps_for(creator_launch_eligible="yes")


@pytest.mark.parametrize("product_type", ["apps", "agents", "tools", "apis", "workflows"])
def test_supported_product_types(product_type):
    assert MarketplacePolicy().supports_product_type(product_type)


def test_product_types_are_case_normalized_for_lookup():
    assert MarketplacePolicy().supports_product_type(" APIS ")


@pytest.mark.parametrize("product_type", ["", "unknown", "binary", None])
def test_unsupported_product_types_are_rejected(product_type):
    assert not MarketplacePolicy().supports_product_type(product_type)


def test_payout_is_blocked_until_settlement_and_verification():
    policy = MarketplacePolicy()
    assert policy.payout_block_reason(
        provider_settled=False,
        creator_verified=True,
        payout_destination_verified=True,
        compliance_cleared=True,
        available_minor=10_000,
        requested_minor=5_000,
    ) == "PROVIDER_SETTLEMENT_REQUIRED"


def test_payout_is_blocked_when_available_balance_is_insufficient():
    assert MarketplacePolicy().payout_block_reason(
        provider_settled=True,
        creator_verified=True,
        payout_destination_verified=True,
        compliance_cleared=True,
        available_minor=4_999,
        requested_minor=5_000,
    ) == "INSUFFICIENT_AVAILABLE_BALANCE"


def test_payout_is_eligible_only_when_all_gates_pass():
    assert MarketplacePolicy().payout_block_reason(
        provider_settled=True,
        creator_verified=True,
        payout_destination_verified=True,
        compliance_cleared=True,
        available_minor=10_000,
        requested_minor=5_000,
    ) is None


def test_payout_policy_does_not_claim_to_execute_a_transfer():
    # This policy only determines eligibility; it exposes no transfer operation.
    assert not hasattr(MarketplacePolicy(), "transfer")
    assert not hasattr(MarketplacePolicy(), "send_payout")
