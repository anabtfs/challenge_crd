#using pretty much the same imports as the rebalance file
import json
from decimal import Decimal
from pathlib import Path
from typing import Any
import pytest #using pytest for testing

#in the "real world" scenario, I would connect to an API, send the paramethers and get the response from it
#but here I have the result already created, simulating this response, so I'll just open and read it
#if it was a real API, I would use the request library, validate the connection, the response code and the response body
#but in this simulation, I'm skipping all of that

#finding and opening response file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESPONSE_FILE = ( PROJECT_ROOT / "portfolio_rebalance" / "data_output" / "rebalance_result.json")
REQUEST_FILE = (PROJECT_ROOT / "portfolio_rebalance" / "data_input" / "portfolio_input.json")

#time to use pytest to load response file 
@pytest.fixture
def rebalance_response() -> dict[str, Any]:
    if not RESPONSE_FILE.exists():
        raise FileNotFoundError(f"API response was not found: {RESPONSE_FILE}" ) #raising error in case json is missing

    #opening json
    with RESPONSE_FILE.open("r", encoding="utf-8") as file:
        return json.load( file, parse_float=Decimal, parse_int=Decimal, ) #converting json floats to decimals

#now lets load the request file to use on tests    
@pytest.fixture
def rebalance_request() -> dict[str, Any]:
    if not REQUEST_FILE.exists():
        raise FileNotFoundError(f"Simulated API request was not found: {REQUEST_FILE}") #raising error in case json is missing

    with REQUEST_FILE.open("r", encoding="utf-8") as file:
        return json.load(file,parse_float=Decimal,parse_int=Decimal,) #converting json floats to decimals