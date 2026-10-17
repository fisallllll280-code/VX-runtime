import pytest

from vxruntime.finance import (
    enforce_drawdown_limit,
    max_drawdown,
    risk_capped_quantity,
    simple_returns,
    validate_close_series,
)


def test_simple_returns():
    assert simple_returns([100, 110, 99]) == pytest.approx((0.1, -0.1))


def test_rejects_invalid_prices():
    for prices in ([], [100], [0, 100], [100, -1]):
        with pytest.raises(ValueError):
            validate_close_series(prices)


def test_max_drawdown():
    assert max_drawdown([100, 120, 90, 105]) == pytest.approx(-0.25)


def test_risk_sizing_obeys_limits():
    quantity = risk_capped_quantity(
        equity=10000, risk_fraction=0.01, entry_price=100,
        stop_price=95, max_notional_fraction=0.5
    )
    assert quantity == pytest.approx(50.0)
    assert quantity * 5 <= 100


def test_invalid_long_stop_is_rejected():
    with pytest.raises(ValueError):
        risk_capped_quantity(
            equity=10000, risk_fraction=0.01,
            entry_price=100, stop_price=101
        )


def test_drawdown_gate():
    assert enforce_drawdown_limit([100, 98, 97], 0.05)
    assert not enforce_drawdown_limit([100, 90], 0.05)
