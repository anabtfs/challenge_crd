Hi, and welcome to my repository!

This was a fun challenge to work through. Before exploring the code, there are a few assumptions and design decisions worth knowing.

## Assumptions

1. All security prices use the same currency. Currency conversion and exchange-rate movements are outside the scope of this solution.
2. All trades use whole units. Fractional quantities are not supported. Implementation is not covering Funds trading, which would allow for decimal quantities.
3. I defined the business rules used by the rebalance calculation. They may differ from the rules used in a real production environment, but keeping them in a separate configuration file makes the solution easier to understand and customise.
4. I treated the input and output JSON files as the request and response bodies of a simulated API:
   * `portfolio_input.json` represents the API request.
   * `rebalance_result.json` represents the API response.

There is no live API or HTTP connection in this challenge. The automated tests begin by loading and validating these files.

## Business rules

The rebalance follows these rules:

1. Calculate all positions that are above their target allocation.
2. Sell whole units, rounding each required sale up.
3. Pool all cash raised from sales.
4. Identify all positions below their target allocation.
5. Evaluate the affordable combinations of whole-unit purchases.
6. Select the combination that produces the smallest total absolute final target variance across the portfolio.
7. Do not purchase another unit if doing so would increase the total portfolio variance.
8. Return all remaining cash as `available_cash`.
9. The current percentages must total 100%.
10. The target percentages must total 100%.

No transaction fees, taxes, currency conversions, deposits, or withdrawals are included.

## Test approach

The automated test suite uses `pytest` to validate the simulated response against the request and the business rules.

The tests cover areas such as:

* Request and response consistency
* Required fields and data types
* Current, target, and final value calculations
* Percentage and variance calculations
* BUY, SELL, and HOLD behaviour
* Whole-unit quantities
* Sale and purchase rounding
* Available cash
* Portfolio-value reconciliation
* Improvement of the overall portfolio variance

The scenarios are also documented in `rebalance.feature`. Each automated test has a matching `RB-###` reference, making it easy to trace the business scenario to its Python implementation.
The feature file also includes manual scenarios for alternative portfolios, boundary conditions, invalid requests, precision, and multi-security allocation. These scenarios demonstrate the wider intended coverage without introducing multiple simulated request and response files beyond the scope of the challenge.
The Gherkin file is currently used as a readable specification and test catalogue; it is not executed directly by pytest.

## Intentional failing test

I deliberately introduced one defect into the rebalance implementation.
The business rule requires a fractional sale quantity to be rounded up to the next whole unit. However, the implementation rounds the quantity down.

For the supplied data:
Required ORCL sale: 45.4545... units
Expected quantity:  -46
Actual quantity:    -45

The scenario `RB-023` and the test `test_sell_quantity_is_rounded_up` detect this mismatch.
I intentionally left the defect in place because I wanted the final test execution to demonstrate that the automation can identify incorrect behaviour rather than simply confirm that the generated response exists.

The expected result is:
31 passed, 1 failed

The failure is therefore expected and documented; it represents a business-rule defect successfully detected by the test suite.

## Running the tests

Create and activate a virtual environment, then install pytest:

#Windows
python -m venv .venv 
.venv\Scripts\Activate.ps1  OR .venv\Scripts\Activate.bat
python -m pip install -r requirements.txt

Run the tests from the project root:

python -m pytest tests\test_rebalance.py -v

#Linux
python -m venv .venv 
source .venv/bin/activate
python -m pip install -r requirements.txt

Run the tests from the project root:

#Windows
python -m pytest tests\test_rebalance.py -v

#Linux
python -m pytest tests/test_rebalance.py -v

## Generating the test report

To run the automated tests and generate a self-contained HTML report:

#Windows
python -m pytest tests\test_rebalance.py -v --html=reports\rebalance_test_report.html --self-contained-html

#Linux
python -m pytest tests/test_rebalance.py -v --html=reports/rebalance_test_report.html --self-contained-html

## Final note

This solution is intentionally scoped to the supplied challenge. With access to a real API, I would extend it with HTTP contract validation, alternative request datasets, error-response testing, authentication, performance checks, and integration into a CI/CD pipeline.

Thanks for taking the time to review everything!

Ana
