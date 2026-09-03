import json #we'll be using json as input and output of this script
from decimal import Decimal, ROUND_FLOOR #using decimal for precision, round_floor to round down units (on purpose)
from pathlib import Path #reading local paths
from typing import Any #using any for type values


# setting up the input and oputput json files
BASE_DIRECTORY = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIRECTORY / "data_input" / "portfolio_input.json"
OUTPUT_FILE = BASE_DIRECTORY / "data_output" / "rebalance_result.json"

ONE_HUNDRED = Decimal("100") #creating 100 as a decimal number to use in calculations later

#reading the input json
def load_json(file_path: Path) -> dict[str, Any]:
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file, parse_float=Decimal, parse_int=Decimal) #convering json floats into decimals


def validate_input(data: dict[str, Any]) -> None:
    account_id = data.get("account_id") #get the account number
    total_assets = data.get("total_assets") #get the total assets
    portfolio_details = data.get("portfolio_details") #get the portfolio details

    #account_id must exists in the json
    if not isinstance(account_id, str) or not account_id.strip(): 
        raise ValueError( "account_id is required." )

    #portfolio_details section must exists in the json
    if portfolio_details is None:
        raise ValueError( "portfolio_details is required." )

    #total_seets could be empty if the portfolio is also empty
    if not portfolio_details:
        if total_assets is not None and total_assets < 0:
            raise ValueError( "total_assets cannot be negative.")
        return

    #but when portfolio details exists, total_assets must also exists 
    if total_assets is None:
        raise ValueError( "total_assets is required when portfolio positions exist.")

    #and when portfolio details exists, total_assets must be greater than 0
    if total_assets <= 0:
        raise ValueError( "when portfolio positions exist, total_assets must be greater than zero. " )

    #portfolio_details is always a list
    if not isinstance(portfolio_details, list):
        raise ValueError( "portfolio_details must be a list." )

    #portfolio_details could be empty in case account has no investments yet, so defining it so calcs later don't break
    if not portfolio_details:
        return

    #defining the fields that are present in each position of the portfolio_details list
    required_fields = {"security", "target_percent", "current_percent", "unit_price",}

    #validating the positions in the portfolio
    for position in portfolio_details:
        missing_fields = required_fields - position.keys()
        if missing_fields:
            raise ValueError(f"position is missing fields: {sorted(missing_fields)}." ) #rise error in case positions are missing

        if position["unit_price"] <= 0:
            raise ValueError("unit_price must be greater than zero.") #making sure I have a price for each stock

    #ensuring target portfolio total adds up
    target_total = sum(position["target_percent"] for position in portfolio_details)

    #raise error in case target total is not 100%
    if target_total != ONE_HUNDRED:
        raise ValueError("target percentages must add up to 100.")

    #ensuring current portfolio total adds up
    current_total = sum(position["current_percent"] for position in portfolio_details)

    #raise error in case target total is not 100%
    if current_total != ONE_HUNDRED:
        raise ValueError("current percentages must add up to 100.")


#starting the calcs
#first, ensure decimal quantities are rounded down so we work with whole units only
def whole_units(quantity: Decimal) -> int:
    return int(quantity.to_integral_value(rounding=ROUND_FLOOR))

#calculating the rebalance 
def calculate_rebalance(data: dict[str, Any]) -> dict[str, Any]:
    validate_input(data) #validating the data_input json to start

    total_assets = data["total_assets"] #get total assets

    result_rows: list[dict[str, Any]] = [] #preparing the output rows list in the same way the input one was set

    #preparing a list of positions that will need to be sold/bought 
    sell_rows: list[dict[str, Any]] = []
    buy_rows: list[dict[str, Any]] = []

    #loop through the positions and calculate the gap, if any
    for position in data["portfolio_details"]:
        current_value = ( total_assets * position["current_percent"] / ONE_HUNDRED ) #checking the total for the current value
        target_value = ( total_assets * position["target_percent"] / ONE_HUNDRED) #checking the total for the target value
        
        #zero: do nothing, positive: buy, negative: sell
        trade_value = target_value - current_value

        #buiding the output for all assets, with the decision to buy, sell or hold
        row = {
            "security": position["security"],
            "target_percent": position["target_percent"],
            "current_percent": position["current_percent"],
            "target_variance_percent": ( position["current_percent"] - position["target_percent"] ), 
            "unit_price": position["unit_price"],
            "current_value": current_value,
            "target_value": target_value,
            "trade_value": trade_value,
            "action": "HOLD", #hardcoded for now, but is updated later
            "shares_to_buy_sell": 0, #hardcoded for now, but is updated later
        }

        result_rows.append(row) #preserving the rows for the output

        #ensuring I process the sale first, so I know how much I can use on the purchase later
        if trade_value < 0:
            sell_rows.append(row)
        elif trade_value > 0:
            buy_rows.append(row)

    #starting with 0 cash available
    available_cash = Decimal("0")

    #calculating how many units I'll need to sell
    for row in sell_rows:
        ideal_units = abs(row["trade_value"]) / row["unit_price"]
        units_to_sell = whole_units(ideal_units) #rounding down on purpose

        row["action"] = "SELL" #if negative, then it'll be a sale
        row["shares_to_buy_sell"] = -units_to_sell

        available_cash += Decimal(units_to_sell) * row["unit_price"] #available cash now has the sale proceeds

    #calculating how many units I'll need to buy using the cash raised above
    for row in buy_rows:
        ideal_units = row["trade_value"] / row["unit_price"] #calculating how many units I'll need tor ebalance
        affordable_units = available_cash / row["unit_price"] #calculating how many units I can get from the money raised

        units_to_buy = min( whole_units(ideal_units), whole_units(affordable_units), ) #use the smaller quantity on the purchase
                           
        row["action"] = "BUY" #if positive, then it'll be a purchase
        row["shares_to_buy_sell"] = units_to_buy

        #deducting the cash used on the purchase from the  available
        available_cash -= Decimal(units_to_buy) * row["unit_price"]

    #calculating how the portfolio looks after the trades
    for row in result_rows:
        traded_units = Decimal(row["shares_to_buy_sell"])
        final_value = ( row["current_value"] + traded_units * row["unit_price"] ) #adding purchases, subtracting sales

        final_percent = final_value / total_assets * ONE_HUNDRED #getting the final portfolio position

        #adding final values to the output
        row["final_value"] = final_value
        row["final_percent"] = final_percent
        row["final_target_variance_percent"] = ( final_percent - row["target_percent"] )

        #removing the trade value from public output
        del row["trade_value"]

    #return the final rebalance result
    return {
        "account_id": data["account_id"],
        "total_assets": total_assets,
        "exact_target_achieved": all(
            row["final_target_variance_percent"] == 0
            for row in result_rows
        ),
        "portfolio_details": result_rows,
        "available_cash": available_cash, #keep any leftover cash in the output, if any
    }


#because I converted json floats to decimals in the begining, I need to convert them back 
def decimal_to_number(value: Any) -> float:
    if isinstance(value, Decimal):
        return float(value)

    #raising error in case of other types mismatches
    raise TypeError(
        f"Object of type {type(value).__name__} is not JSON serialisable."
    )

#creating the output in json format
def write_json(file_path: Path, data: dict[str, Any]) -> None:
    with file_path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=2,
            default=decimal_to_number,
        ) #keeping encoding and indentation for better readability
        file.write("\n") #writting into the file

#using everything I created so far to run the program
def main() -> None:
    portfolio_data = load_json(INPUT_FILE) #loading input data
    rebalance_result = calculate_rebalance(portfolio_data) #calculating the rebalance
    write_json(OUTPUT_FILE, rebalance_result) #creating the json output
    print(f"Rebalance result written to: {OUTPUT_FILE}") #printing where the file is created

#running main
if __name__ == "__main__":
    main()