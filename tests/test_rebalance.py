#again, almost the same imports as the rebalance
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from typing import Any

PERCENTAGE_SCALE = Decimal("0.00000001") #setting 8 decimal places for percentage cals

#checking that I can load the file and add into a dictionary
def test_rebalance_response_is_loaded( rebalance_response: dict[str, Any],) -> None:
    """RB-001: Load the rebalance response successfully"""
    assert isinstance(rebalance_response, dict)
    assert rebalance_response

#checking that the response has all the fields required
def test_rebalance_response_contains_required_fields( rebalance_response: dict[str, Any],) -> None:
    """RB-002: Rebalance response contains required fields"""
    required_fields = {"account_id","total_assets","exact_target_achieved","portfolio_details","available_cash",}
    assert required_fields.issubset(rebalance_response.keys())

#checking that the response has the correct data types
def test_rebalance_response_fields_have_expected_types(rebalance_response: dict[str, Any],) -> None:
    """RB-003: Rebalance response fields have expected types"""
    assert isinstance(rebalance_response["account_id"], str)
    assert isinstance(rebalance_response["total_assets"], Decimal)
    assert isinstance(rebalance_response["exact_target_achieved"], bool)
    assert isinstance(rebalance_response["portfolio_details"], list)
    assert isinstance(rebalance_response["available_cash"], Decimal)

#checking that the response always has a valid account id sent
def test_account_id_is_not_empty(rebalance_response: dict[str, Any],) -> None:
    """RB-004: Account ID is not empty"""
    account_id = rebalance_response["account_id"]
    assert account_id.strip()

#checking that response contains current positions
def test_rebalance_response_contains_positions(rebalance_response: dict[str, Any],) -> None:
    """RB-005: Rebalance response contains positions"""
    portfolio_details = rebalance_response["portfolio_details"]
    assert portfolio_details

#checking that every position has the right fields
def test_each_position_contains_required_fields(rebalance_response: dict[str, Any],) -> None:
    """RB-006: Return all required fields for every position"""
    required_fields = {"security","target_percent","current_percent","target_variance_percent","unit_price","current_value",
                       "target_value","action","shares_to_buy_sell","final_value","final_percent","final_target_variance_percent",}

    for position in rebalance_response["portfolio_details"]:
        missing_fields = required_fields - position.keys()

        assert not missing_fields, (f"Position {position.get('security', '<unknown>')} is missing fields: {sorted(missing_fields)}")

#checking the data types on each position returned
def test_each_position_has_expected_field_types(rebalance_response: dict[str, Any],) -> None:
    """RB-007: Return position fields with the expected data types"""
    numeric_fields = {"target_percent","current_percent","target_variance_percent","unit_price","current_value","target_value",
        "shares_to_buy_sell","final_value","final_percent","final_target_variance_percent",}

    for position in rebalance_response["portfolio_details"]:
        security = position["security"]
        assert isinstance(security, str), (f"security should be a string, but received {type(security).__name__}"
        )

        assert security.strip(), "security should not be empty"

        assert isinstance(position["action"], str), (f"{security}: action should be a string")

        for field in numeric_fields:
            assert isinstance(position[field], Decimal), (f"{security}: {field} should be Decimal, but received {type(position[field]).__name__}")

#checking that the only possible actions are either buy, sell or hold
def test_each_position_has_a_supported_action(rebalance_response: dict[str, Any],) -> None:
    """RB-008: Return only supported trade actions"""
    supported_actions = {"BUY", "SELL", "HOLD"}

    for position in rebalance_response["portfolio_details"]:
        assert position["action"] in supported_actions, (f"{position['security']}: unsupported action '{position['action']}'")

#checking that purchase quantities are positive, sell quantities are negative, and hold quantities are zero
def test_trade_quantity_matches_action(rebalance_response: dict[str, Any],) -> None:
    """RB-009: Trade quantities match the action being taken"""

    for position in rebalance_response["portfolio_details"]:
        security = position["security"]
        action = position["action"]
        quantity = position["shares_to_buy_sell"]

        if action == "BUY":
            assert quantity > 0, (f"{security}: BUY quantity should be positive, but received {quantity}")

        elif action == "SELL":
            assert quantity < 0, (f"{security}: SELL quantity should be negative, but received {quantity}")

        elif action == "HOLD":
            assert quantity == 0, (f"{security}: HOLD quantity should be zero, but received {quantity}")

        else:
            raise AssertionError(f"{security}: unsupported action '{action}'")

#checking that each unit is a whole unit
def test_all_trade_quantities_are_whole_units(rebalance_response: dict[str, Any],) -> None:
    """RB-010: Return only whole-unit trade quantities"""

    for position in rebalance_response["portfolio_details"]:
        security = position["security"]
        quantity = position["shares_to_buy_sell"]

        assert quantity == quantity.to_integral_value(), (f"{security}: EQT trade quantity should be a whole unit, but received {quantity}")

#checking that current value is using total assets value and current portfolio %
def test_current_value_is_calculated_correctly(rebalance_response: dict[str, Any],) -> None:
    """RB-011: Calculate current position value correctly"""
    total_assets = rebalance_response["total_assets"]

    for position in rebalance_response["portfolio_details"]:
        expected_current_value = (total_assets * position["current_percent"]/ Decimal("100"))

        assert position["current_value"] == expected_current_value, (f"{position['security']}: expected current_value "
            f"{expected_current_value}, but received {position['current_value']}")

#checking that target value is using total assets value and target portfolio %
def test_target_value_is_calculated_correctly(rebalance_response: dict[str, Any],) -> None:
    """RB-012: Calculate target position value correctly"""
    total_assets = rebalance_response["total_assets"]

    for position in rebalance_response["portfolio_details"]:
        expected_target_value = (total_assets * position["target_percent"] / Decimal("100"))

        assert position["target_value"] == expected_target_value, (f"{position['security']}: expected target_value "
            f"{expected_target_value}, but received {position['target_value']}")

#checking if unitial variance is the current - target %
def test_target_variance_is_calculated_correctly(rebalance_response: dict[str, Any],) -> None:
    """RB-013: Calculate target position variance correctly"""

    for position in rebalance_response["portfolio_details"]:
        expected_variance = (position["current_percent"] - position["target_percent"])

        assert (position["target_variance_percent"] == expected_variance), (f"{position['security']}: expected target variance "
            f"{expected_variance}, but received {position['target_variance_percent']}")

#checking that current % sum to 100%
def test_current_percentages_sum_to_one_hundred(rebalance_response: dict[str, Any],) -> None:
    """RB-014: Current percentages sum to 100%"""

    total_current_percent = sum(
        (
            position["current_percent"]
            for position in rebalance_response["portfolio_details"]
        ),
        start=Decimal("0"),
    )

    assert total_current_percent == Decimal("100"), (f"Current percentages should total 100%, but totalled {total_current_percent}%")

#checking that target % sum to 100%
def test_target_percentages_sum_to_one_hundred(rebalance_response: dict[str, Any],) -> None:
    """RB-015: Target percentages sum to 100%"""

    total_target_percent = sum(
        (
            position["target_percent"]
            for position in rebalance_response["portfolio_details"]
        ),
        start=Decimal("0"),
    )

    assert total_target_percent == Decimal("100"), (f"Target percentages should total 100%, but totalled {total_target_percent}%")

#checking that final value after the proposed trade
def test_final_value_reflects_the_executed_trade(rebalance_response: dict[str, Any],) -> None:
    """RB-016: Calculate final position value correctly"""

    for position in rebalance_response["portfolio_details"]:
        expected_final_value = (position["current_value"] + (position["shares_to_buy_sell"] * position["unit_price"]))

        assert position["final_value"] == expected_final_value, (f"{position['security']}: expected final_value "
            f"{expected_final_value}, but received {position['final_value']}")

#checking that final % is calculated using final value and total assets
def test_final_percent_is_calculated_correctly(rebalance_response: dict[str, Any],) -> None:
    """RB-017: Calculate final position percentage correctly"""
    total_assets = rebalance_response["total_assets"]

    for position in rebalance_response["portfolio_details"]:
        expected_final_percent = (position["final_value"] / total_assets * Decimal("100")).quantize(PERCENTAGE_SCALE)

        assert (position["final_percent"] == expected_final_percent), (f"{position['security']}: expected final_percent "
            f"{expected_final_percent}, but received {position['final_percent']}" )

#check final target variance
def test_final_target_variance_is_calculated_correctly(rebalance_response: dict[str, Any],) -> None:
    """RB-018: Calculate final target variance correctly"""

    for position in rebalance_response["portfolio_details"]:
        expected_final_variance = (position["final_percent"] - position["target_percent"]).quantize(PERCENTAGE_SCALE)

        assert (position["final_target_variance_percent"]== expected_final_variance), (f"{position['security']}: expected "
            f"final_target_variance_percent {expected_final_variance}, but received {position['final_target_variance_percent']}")


#checking that exact target achieved is true 
def test_exact_target_achieved_matches_final_variances(rebalance_response: dict[str, Any],) -> None:
    """RB-019: Match the exact-target flag to the final variances"""
    expected_exact_target_achieved = all(position["final_target_variance_percent"] == Decimal("0")
        for position in rebalance_response["portfolio_details"]
    )

    assert (rebalance_response["exact_target_achieved"] is expected_exact_target_achieved), (f"Expected exact_target_achieved to be "
        f"{expected_exact_target_achieved}, but received {rebalance_response['exact_target_achieved']}")


#checking available cash after proposed trades
def test_available_cash_is_calculated_correctly(rebalance_response: dict[str, Any],) -> None:
    """RB-020: Calculate available cash correctly"""
    portfolio_details = rebalance_response["portfolio_details"]
    total_sale_proceeds = sum(
        (
            abs(position["shares_to_buy_sell"]) * position["unit_price"]
            for position in portfolio_details
            if position["action"] == "SELL"
        ),
        start=Decimal("0"),
    )

    total_purchase_cost = sum(
        (
            position["shares_to_buy_sell"] * position["unit_price"]
            for position in portfolio_details
            if position["action"] == "BUY"
        ),
        start=Decimal("0"),
    )

    expected_available_cash = (total_sale_proceeds - total_purchase_cost)

    assert (rebalance_response["available_cash"] == expected_available_cash), (f"Expected available_cash to be "
        f"{expected_available_cash}, but received {rebalance_response['available_cash']}")



#checking that the rebalance preserves the total portfolio value after proposed trades
def test_total_portfolio_value_is_preserved(rebalance_response: dict[str, Any],) -> None:
    """RB-021: Preserve total portfolio value after proposed trades"""
    total_final_position_value = sum(
        (
            position["final_value"]
            for position in rebalance_response["portfolio_details"]
        ),
        start=Decimal("0"),
    )

    final_economic_value = (total_final_position_value + rebalance_response["available_cash"])

    assert final_economic_value == rebalance_response["total_assets"], (f"Expected final portfolio value to be "
        f"{rebalance_response['total_assets']}, but positions and cash total {final_economic_value}" )


#checking that the final portfolio reduces variance enough
def test_rebalance_reduces_total_portfolio_variance(rebalance_response: dict[str, Any],) -> None:
    """RB-022: Rebalance reduces total portfolio variance"""
    initial_total_variance = sum(
        (
            abs(position["target_variance_percent"])
            for position in rebalance_response["portfolio_details"]
        ),
        start=Decimal("0"),
    )

    final_total_variance = sum(
        (
            abs(position["final_target_variance_percent"])
            for position in rebalance_response["portfolio_details"]
        ),
        start=Decimal("0"),
    )

    assert final_total_variance < initial_total_variance, (f"Expected rebalance to reduce total variance, "
        f"but initial variance was {initial_total_variance} and final variance was {final_total_variance}" )


#checking rouding up on sales (this is the business rule I didn't follow when coding the rebalance)
def test_sell_quantity_is_rounded_up(rebalance_response: dict[str, Any],) -> None:
    """RB-023: Round an sale quantity up"""

    for position in rebalance_response["portfolio_details"]:
        if position["action"] != "SELL":
            continue

        excess_value = ( position["current_value"] - position["target_value"])
        expected_units_to_sell = (excess_value / position["unit_price"]).to_integral_value(rounding=ROUND_CEILING)
        expected_quantity = -expected_units_to_sell

        assert (position["shares_to_buy_sell"] == expected_quantity), (f"{position['security']}: expected SELL quantity "
            f"{expected_quantity}, but received {position['shares_to_buy_sell']}")

#checking rouding down on purchases 
def test_buy_quantity_is_rounded_down(rebalance_response: dict[str, Any],) -> None:
    """RB-024: Round an purchase quantity down"""

    for position in rebalance_response["portfolio_details"]:
        if position["action"] != "BUY":
            continue

        value_below_target = (position["target_value"] - position["current_value"])
        expected_units_to_buy = (value_below_target / position["unit_price"]).to_integral_value(rounding=ROUND_FLOOR)

        assert (position["shares_to_buy_sell"] == expected_units_to_buy), (f"{position['security']}: expected BUY quantity "
            f"{expected_units_to_buy}, but received {position['shares_to_buy_sell']}")

#checking that purchases don't use more cash than raised on sales
def test_purchase_cost_does_not_exceed_sale_proceeds(rebalance_response: dict[str, Any],) -> None:
    """RB-025: Purchase cost does not exceed sale proceeds"""
    portfolio_details = rebalance_response["portfolio_details"]
    total_sale_proceeds = sum(
        (
            abs(position["shares_to_buy_sell"]) * position["unit_price"]
            for position in portfolio_details
            if position["action"] == "SELL"
        ),
        start=Decimal("0"),
    )

    total_purchase_cost = sum(
        (
            position["shares_to_buy_sell"] * position["unit_price"]
            for position in portfolio_details
            if position["action"] == "BUY"
        ),
        start=Decimal("0"),
    )

    assert total_purchase_cost <= total_sale_proceeds, (f"Purchase cost {total_purchase_cost} exceeds sale proceeds {total_sale_proceeds}")
    assert rebalance_response["available_cash"] >= Decimal("0"), (f"available_cash should not be negative, but received {rebalance_response['available_cash']}")


#checking that sum of available cash and final positions is 100% of total assets
def test_final_percentages_and_cash_sum_to_one_hundred(rebalance_response: dict[str, Any],) -> None:
    """RB-026: Final percentages and cash sum to 100%"""
    total_final_position_percent = sum(
        (
            position["final_percent"]
            for position in rebalance_response["portfolio_details"]
        ),
        start=Decimal("0"),
    )

    available_cash_percent = (rebalance_response["available_cash"] / rebalance_response["total_assets"] * Decimal("100")).quantize(PERCENTAGE_SCALE)
    total_final_percent = (total_final_position_percent + available_cash_percent).quantize(PERCENTAGE_SCALE)

    assert total_final_percent == Decimal("100").quantize(PERCENTAGE_SCALE), (f"Expected final positions and cash to total 100%, but received {total_final_percent}%")

#checking that for the proposed hold, no changes are made
def test_hold_positions_remain_unchanged(rebalance_response: dict[str, Any],) -> None:
    """RB-027: Hold positions remain unchanged"""

    for position in rebalance_response["portfolio_details"]:
        if position["action"] != "HOLD":
            continue

        security = position["security"]

        assert position["shares_to_buy_sell"] == Decimal("0"), (f"{security}: HOLD quantity should be zero, but received {position['shares_to_buy_sell']}")

        assert position["final_value"] == position["current_value"], (f"{security}: HOLD final_value should remain {position['current_value']}, but received {position['final_value']}")

        assert position["final_percent"] == position["current_percent"], (f"{security}: HOLD final_percent should remain {position['current_percent']}, but received {position['final_percent']}")

#checking that proposed trades moves position closer to target
def test_each_trade_reduces_position_variance(rebalance_response: dict[str, Any],) -> None:
    """RB-028: Each trade reduces position variance"""

    for position in rebalance_response["portfolio_details"]:
        if position["action"] == "HOLD":
            continue

        initial_absolute_variance = abs(position["target_variance_percent"])
        final_absolute_variance = abs(position["final_target_variance_percent"])

        assert final_absolute_variance < initial_absolute_variance, (f"{position['security']}: {position['action']} did not move the position closer to target. "
            f"Initial absolute variance was {initial_absolute_variance}, but final absolute variance was {final_absolute_variance}")

#checking for dupplicate stocks on response
def test_each_security_appears_once(rebalance_response: dict[str, Any],) -> None:
    """RB-029: Each security appears only once in the rebalance response"""
    securities = [position["security"]
        for position in rebalance_response["portfolio_details"]
    ]

    duplicate_securities = {security
        for security in securities
        if securities.count(security) > 1
    }

    assert not duplicate_securities, (f"Response contains duplicate securities: {sorted(duplicate_securities)}")

#checking that request details are preserved in the response
def test_response_preserves_request_details(rebalance_request: dict[str, Any],rebalance_response: dict[str, Any],) -> None:
    """RB-030: Verify that request details are preserved in the response."""

    assert (rebalance_response["account_id"] == rebalance_request["account_id"])
    assert (rebalance_response["total_assets"] == rebalance_request["total_assets"])

    request_positions = {position["security"]: position for position in rebalance_request["portfolio_details"]}

    response_positions = {position["security"]: position for position in rebalance_response["portfolio_details"]}

    assert response_positions.keys() == request_positions.keys()
    preserved_fields = {"target_percent","current_percent","unit_price",}

    for security, request_position in request_positions.items():
        response_position = response_positions[security]

        for field in preserved_fields:
            assert (response_position[field] == request_position[field]), (f"{security}: expected {field} "
                f"{request_position[field]}, but received {response_position[field]}")

#checking that proposed actions match variations
def test_action_matches_position_allocation(rebalance_response: dict[str, Any],) -> None:
    """RB-031: Verify that actions match position allocations."""

    for position in rebalance_response["portfolio_details"]:
        security = position["security"]
        variance = position["target_variance_percent"]
        action = position["action"]

        if variance > Decimal("0"):
            assert action == "SELL", (f"{security}: position is above target and should be SELL, but received {action}")

        elif variance == Decimal("0"):
            assert action == "HOLD", (f"{security}: position is on target and should be HOLD, but received {action}")

        else:
            assert action in {"BUY", "HOLD"}, (f"{security}: position is below target and should be BUY or HOLD, but received {action}")

#checking that positions are valid
def test_position_values_are_within_valid_ranges(rebalance_response: dict[str, Any],) -> None:
    """RB-032: Verify that position values are within valid ranges."""

    for position in rebalance_response["portfolio_details"]:
        security = position["security"]

        assert position["unit_price"] > Decimal("0"), (f"{security}: unit_price should be greater than zero, but received {position['unit_price']}")

        percentage_fields = {"target_percent","current_percent","final_percent",}

        for field in percentage_fields:
            assert Decimal("0") <= position[field] <= Decimal("100"), (f"{security}: {field} should be between 0 and 100, but received {position[field]}")

        monetary_fields = {"current_value","target_value","final_value",}

        for field in monetary_fields:
            assert position[field] >= Decimal("0"), (f"{security}: {field} should not be negative, but received {position[field]}")


