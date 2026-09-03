# This feature currently documents the tests/test_rebalance.py and manual scenarios that would complement the automation
# Scenario IDs provide traceability between the business specification and the Python automation.

# RB-023 is intentionally expected to fail. 

@rebalance
Feature: Validate a portfolio rebalance
  As a portfolio service consumer
  I want to have my portfolio rebalanced
  So that target allocations are always met 

  Rule: The simulated API response can be loaded and has the required contract

    @automated @smoke @RB-001
    Scenario: Load the rebalance response successfully
      Given the simulated rebalance API has returned a response body
      When the response JSON is loaded
      Then the response should be a non-empty dictionary

    @automated @contract @RB-002
    Scenario: Return all required top-level fields
      Given the rebalance response has been loaded
      When the top-level response fields are inspected
      Then the response should contain:
        | field                 |
        | account_id            |
        | total_assets          |
        | exact_target_achieved |
        | portfolio_details     |
        | available_cash        |

    @automated @contract @RB-003
    Scenario: Return top-level fields with the expected data types
      Given the rebalance response has been loaded
      When the top-level field types are inspected
      Then account_id should be a string
      And total_assets should be a decimal number
      And exact_target_achieved should be Boolean
      And portfolio_details should be a list
      And available_cash should be a decimal number

    @automated @contract @RB-004
    Scenario: Return a non-empty account identifier
      Given the rebalance response has been loaded
      When account_id is inspected
      Then account_id should contain a non-whitespace value

    @automated @contract @RB-005
    Scenario: Return positions for the populated portfolio
      Given the simulated response represents a populated portfolio
      When portfolio_details is inspected
      Then portfolio_details should not be empty

    @automated @contract @RB-006
    Scenario: Return all required fields for every position
      Given the populated rebalance response has been loaded
      When each portfolio position is inspected
      Then every position should contain:
        | field                         |
        | security                      |
        | target_percent                |
        | current_percent               |
        | target_variance_percent       |
        | unit_price                    |
        | current_value                 |
        | target_value                  |
        | action                        |
        | shares_to_buy_sell            |
        | final_value                   |
        | final_percent                 |
        | final_target_variance_percent |

    @automated @contract @RB-007
    Scenario: Return position fields with the expected data types
      Given the populated rebalance response has been loaded
      When each portfolio position field is inspected
      Then security should be a non-empty string
      And action should be a string
      And every financial and quantity field should be a decimal number

    @automated @contract @RB-008
    Scenario: Return only supported trade actions
      Given the populated rebalance response has been loaded
      When each position action is inspected
      Then every action should be one of:
        | action |
        | BUY    |
        | SELL   |
        | HOLD   |

    @automated @contract @RB-009
    Scenario: Match the trade quantity sign to its action
      Given the populated rebalance response has been loaded
      When each action and trade quantity are compared
      Then a BUY quantity should be positive
      And a SELL quantity should be negative
      And a HOLD quantity should be zero

    @automated @contract @RB-010
    Scenario: Return only whole-unit trade quantities
      Given the portfolio contains  instruments only
      When every shares_to_buy_sell value is inspected
      Then every trade quantity should be a whole number

  Rule: Initial and target portfolio values are calculated correctly

    @automated @calculation @RB-011
    Scenario: Calculate current position value correctly
      Given a position has a current percentage
      And the response contains total_assets
      When current_value is independently calculated
      Then current_value should equal total_assets multiplied by current_percent divided by 100

    @automated @calculation @RB-012
    Scenario: Calculate target position value correctly
      Given a position has a target percentage
      And the response contains total_assets
      When target_value is independently calculated
      Then target_value should equal total_assets multiplied by target_percent divided by 100

    @automated @calculation @RB-013
    Scenario: Calculate initial target variance correctly
      Given a position has current_percent and target_percent
      When target_variance_percent is independently calculated
      Then target_variance_percent should equal current_percent minus target_percent

    @automated @validation @RB-014
    Scenario: Ensure current percentages total 100 percent
      Given the populated rebalance response has been loaded
      When all current_percent values are added
      Then the total should equal 100%

    @automated @validation @RB-015
    Scenario: Ensure target percentages total 100 percent
      Given the populated rebalance response has been loaded
      When all target_percent values are added
      Then the total should equal 100%

  Rule: Final portfolio values and status are calculated correctly

    @automated @calculation @RB-016
    Scenario: Calculate final position value from the executed trade
      Given a position has a current value, unit price, and signed trade quantity
      When final_value is independently calculated
      Then final_value should equal current_value plus shares_to_buy_sell multiplied by unit_price

    @automated @calculation @RB-017
    Scenario: Calculate final position percentage correctly
      Given a position has a final value
      And the response contains total_assets
      When final_percent is independently calculated to the configured percentage scale
      Then final_percent should equal final_value divided by total_assets multiplied by 100

    @automated @calculation @RB-018
    Scenario: Calculate final target variance correctly
      Given a position has final_percent and target_percent
      When final_target_variance_percent is independently calculated
      Then final_target_variance_percent should equal final_percent minus target_percent

    @automated @calculation @RB-019
    Scenario: Match the exact-target flag to the final variances
      Given all final position variances have been calculated
      When exact_target_achieved is evaluated
      Then it should be true only when every final_target_variance_percent equals zero

    @automated @cash @calculation @RB-020
    Scenario: Calculate available cash correctly
      Given SELL trades raise cash
      And BUY trades spend cash
      When available_cash is independently calculated
      Then available_cash should equal total sale proceeds minus total purchase cost

    @automated @reconciliation @RB-021
    Scenario: Preserve total portfolio value
      Given no transaction fees, taxes, deposits, or withdrawals apply
      When all final position values and available_cash are added
      Then the total should equal total_assets

    @automated @optimisation @RB-022
    Scenario: Reduce total portfolio variance
      Given the portfolio requires rebalancing
      When the initial and final total absolute variances are compared
      Then the final total absolute variance should be lower than the initial total absolute variance

  Rule: Trades follow the confirmed whole-unit rounding and funding rules

    @automated @rounding @RB-023 @known-defect 
    Scenario: Round a sale quantity up
      Given an  position is above its target
      And the required sale quantity contains a fractional unit
      When the required sale quantity is calculated
      Then the sale quantity should be rounded up to the next whole unit
      And shares_to_buy_sell should contain the negative rounded quantity

    @automated @rounding @RB-024
    Scenario: Round a purchase quantity down
      Given an  position is below its target
      And the required purchase quantity contains a fractional unit
      When the required purchase quantity is calculated
      Then the purchase quantity should be rounded down to a whole unit
      And shares_to_buy_sell should contain the positive rounded quantity

    @automated @cash @RB-025
    Scenario: Do not spend more than the cash raised by sales
      Given purchases may be funded only by sale proceeds
      When total purchase cost and total sale proceeds are compared
      Then total purchase cost should not exceed total sale proceeds
      And available_cash should not be negative

    @automated @reconciliation @RB-026
    Scenario: Ensure final positions and cash total 100 percent
      Given the rebalance may leave available cash
      When all final position percentages and the available cash percentage are added
      Then the total should equal 100%

    @automated @action @RB-027
    Scenario: Leave HOLD positions unchanged
      Given a position has action "HOLD"
      When its final result is inspected
      Then shares_to_buy_sell should equal zero
      And final_value should equal current_value
      And final_percent should equal current_percent

    @automated @optimisation @RB-028
    Scenario: Ensure every executed trade reduces its position variance
      Given a position has action "BUY" or "SELL"
      When its initial and final absolute variances are compared
      Then its final absolute variance should be lower than its initial absolute variance

    @automated @contract @RB-029
    Scenario: Return each security only once
      Given the populated rebalance response has been loaded
      When all returned security identifiers are inspected
      Then no security should appear more than once

    @automated @contract @RB-030
    Scenario: Preserve request details in the response
      Given a valid rebalance request has been submitted
      When the rebalance response is returned
      Then account_id should match the request
      And total_assets should match the request
      And every requested security should appear exactly once
      And target_percent should remain unchanged for every security
      And current_percent should remain unchanged for every security
      And unit_price should remain unchanged for every security


    @automated @action @RB-031
    Scenario: Match each action to the position allocation
      Given the portfolio positions have been compared with their targets
      When the rebalance actions are inspected
      Then a position above target should have action "SELL"
      And a position exactly on target should have action "HOLD"
      And a position below target should have action "BUY" or "HOLD"
      But it should be "HOLD" only when no whole unit can be purchased


    @automated @validation @RB-032
    Scenario: Return position values within valid ranges
      Given the populated rebalance response has been loaded
      When the numeric position values are inspected
      Then every unit_price should be greater than zero
      And every current, target, and final percentage should be between 0% and 100%
      And every current, target, and final monetary value should be non-negative

  Rule: Alternative portfolios and boundary conditions are validated

    @manual @rounding @boundary @RB-033
    Scenario: Sell an exactly divisible number of units
      Given a position is above target
      And the excess value is exactly divisible by the unit price
      When the portfolio is rebalanced
      Then the exact whole-unit quantity should be sold
      And no additional rounding should be applied


    @manual @rounding @boundary @RB-034
    Scenario: Buy an exactly divisible number of units
      Given a position is below target
      And its allocated proceeds are exactly divisible by the unit price
      When the portfolio is rebalanced
      Then the exact whole-unit quantity should be purchased
      And no proceeds should remain from that allocation  

    @manual @cash @boundary @RB-035
    Scenario: Hold an underweight position when one unit cannot be afforded
      Given a position is below target
      And the available proceeds are less than its unit price
      When the portfolio is rebalanced
      Then the position should not receive a purchase
      And its action should be "HOLD"
      And the unused proceeds should remain available_cash

    @manual @cash @RB-036
    Scenario: Return leftover sale proceeds as available cash
      Given the sale proceeds cannot be fully invested using whole units
      When the portfolio is rebalanced
      Then purchases should not exceed the sale proceeds
      And the unspent amount should be returned as available_cash

    @manual @cash @multiple-securities @RB-037
    Scenario: Pool proceeds from multiple sales before purchasing
      Given multiple positions are above target
      And multiple positions are below target
      When the portfolio is rebalanced
      Then all required sales should be calculated first
      And all sale proceeds should be pooled
      And purchases should be funded from the pooled proceeds

    @manual @optimisation @multiple-securities @RB-038
    Scenario: Select the purchase combination with the smallest portfolio variance
      Given multiple positions are below target
      And the proceeds cannot fund every desired purchase
      And multiple whole-unit purchase combinations are possible
      When the portfolio is rebalanced
      Then the selected combination should produce the smallest total absolute final target variance
      And the total purchase cost should not exceed the sale proceeds

    @manual @optimisation @RB-039
    Scenario: Consider unit prices when selecting the optimal allocation
      Given multiple positions are below target by different amounts
      And the positions have different unit prices
      When the portfolio is rebalanced
      Then purchases should not be prioritised solely by the largest initial variance
      And the selected quantities should produce the smallest achievable portfolio variance

    @manual @hold @RB-040
    Scenario: Leave an already-balanced portfolio unchanged
      Given every current percentage equals its target percentage
      When the portfolio is rebalanced
      Then every action should be "HOLD"
      And every trade quantity should be zero
      And available_cash should be zero
      And exact_target_achieved should be true

  Rule: Invalid requests and additional operational conditions are validated manually

    @manual @validation @boundary @RB-041
    Scenario Outline: Reject target percentages that do not total 100 percent
      Given the target percentages total <total>%
      When the portfolio is submitted
      Then the request should be rejected
      And the error should state that target percentages must total 100%

      Examples:
        | total  |
        | 99.99  |
        | 100.01 |

    @manual @validation @boundary @RB-042
    Scenario Outline: Reject current percentages that do not total 100 percent
      Given the current percentages total <total>%
      When the portfolio is submitted
      Then the request should be rejected
      And the error should state that current percentages must total 100%

      Examples:
        | total  |
        | 99.99  |
        | 100.01 |

    @manual @validation @negative @RB-043
    Scenario Outline: Reject a request with a missing required field
      Given the request does not contain <field>
      When the portfolio is submitted
      Then the request should be rejected
      And the error should identify "<field>" as missing
      And no rebalance result should be returned

      Examples:
        | field             |
        | account_id        |
        | total_assets      |
        | portfolio_details |
        | security          |
        | target_percent    |
        | current_percent   |
        | unit_price        |

    @manual @validation @negative @RB-044
    Scenario Outline: Reject a field with an invalid data type
      Given <field> contains <invalid_value>
      When the portfolio is submitted
      Then the request should be rejected
      And the error should identify "<field>" as invalid
      And no partial rebalance result should be returned

      Examples:
        | field             | invalid_value       |
        | account_id        | a numeric value     |
        | total_assets      | a text value        |
        | portfolio_details | a non-list value    |
        | security          | a numeric value     |
        | target_percent    | a text value        |
        | current_percent   | a text value        |
        | unit_price        | a text value        |

    @manual @validation @negative @RB-045
    Scenario: Reject a blank account identifier
      Given account_id is empty or contains only whitespace
      When the portfolio is submitted
      Then the request should be rejected
      And the error should identify account_id as invalid

    @manual @validation @boundary @RB-046
    Scenario Outline: Reject a non-positive total asset value
      Given total_assets is <value>
      When the portfolio is submitted
      Then the request should be rejected
      And the error should identify total_assets as invalid

      Examples:
        | value |
        | 0     |
        | -1    |

    @manual @validation @boundary @RB-047
    Scenario Outline: Reject a non-positive unit price
      Given a position has unit_price <value>
      When the portfolio is submitted
      Then the request should be rejected
      And the error should identify unit_price as invalid

      Examples:
        | value |
        | 0     |
        | -1    |

    @manual @precision @RB-048
    Scenario: Calculate trades accurately when unit prices contain decimals
      Given a valid portfolio contains securities with decimal unit prices
      When the portfolio is rebalanced
      Then all monetary calculations should preserve the documented precision
      And every trade quantity should remain a whole number
      And the final portfolio value should reconcile with total_assets

    @manual @optimisation @RB-049
    Scenario: Accept the closest achievable result when the exact target cannot be reached
      Given whole-unit restrictions prevent one or more positions from reaching exactly zero variance
      When the portfolio is rebalanced
      Then the selected trades should produce the smallest achievable total absolute portfolio variance
      And exact_target_achieved should be false
      And any unused proceeds should remain available_cash

    @manual @boundary @RB-050
    Scenario: Process a large valid portfolio without numeric overflow
      Given a valid request contains large monetary values and many positions
      When the portfolio is rebalanced
      Then the calculation should complete successfully
      And no numeric value should overflow
      And the final portfolio value should reconcile with total_assets

    @manual @determinism @RB-051
    Scenario: Produce the same result for repeated identical requests
      Given the same valid portfolio request is available
      When the request is submitted repeatedly without changing any input
      Then every response should contain the same trade quantity for each security
      And every response should contain the same available_cash
      And every response should contain the same final portfolio variance

    @manual @validation @negative @RB-052
    Scenario: Reject malformed JSON
      Given the request body is not valid JSON
      When the request is submitted
      Then the request should be rejected
      And the response should contain a clear request-format error
      And no rebalance result should be returned
