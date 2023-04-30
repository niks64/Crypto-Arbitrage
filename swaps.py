from decimal import Decimal
from etherscan import Etherscan
import math
import sushiswap
import uniswap


exchanges = ["uniswap", "sushiswap"]
modules = {
    "uniswap": __import__("uniswap"),
    "sushiswap": __import__("sushiswap")
}

etherscan_api_key = "I1D8DNPTT65ZR27H46U4ZQW1TEQFDHQFRY"

def swapTuple(tup):
    return (tup[1], tup[0])

def getGas():
    eth = Etherscan(etherscan_api_key)
    gas_oracle = eth.get_gas_oracle()
    return min(Decimal(15),Decimal(gas_oracle["SafeGasPrice"]))

def checkSwap(optimal_size, pair, amts, spot_prices, gas_cost):
    exchange_order = ("uniswap", "sushiswap")

    if amts[1] > amts[0]:
        amts = swapTuple(amts)
        exchange_order = swapTuple(exchange_order)
        spot_prices = [spot_prices[1], spot_prices[0]]
    
    first_out = amts[0]
    final_out = first_out * Decimal(0.995) * spot_prices[1][1] * Decimal(0.997) - (gas_cost / uniswap.token_values[pair[1]])

    if final_out > optimal_size:
        return (optimal_size, final_out, pair, exchange_order, amts[0])
    else:
        return None
    # uniswap_price = prices[0]
    # sushiswap_price = prices[1]

    # if (Decimal(abs(uniswap_price - sushiswap_price)) / (uniswap_price)) > Decimal(0.05):
    #     return True

def printSwap(swap):
    print("Swap", swap[0], "of", swap[2][1], "for about", swap[4], "of", swap[2][0], "on", swap[3][0], "and swap it for about", swap[1], "of", swap[2][1], "on", swap[3][1])
    print("Profit: $", (swap[1] - swap[0]) * uniswap.token_values[swap[2][1]])

def getSwap(pair, gas_cost):

    # Get the optimum size for the transaction
    reserve_0 = Decimal(sushiswap.pairs_info[pair]['reserve0'])
    reserve_1 = Decimal(sushiswap.pairs_info[pair]['reserve1'])
    optimal_size = (Decimal(math.sqrt(gas_cost)) * reserve_1) / (Decimal(math.sqrt(reserve_0 * Decimal(uniswap.token_values[pair[0]]))) - Decimal(math.sqrt(gas_cost)))
    optimal_size *= Decimal(5)
    if optimal_size < Decimal(0) or optimal_size > Decimal(100000):
        return None

    # Get Spot Value and USD value of the pair
    spot_prices = []
    for e in exchanges:
        spot_prices.append(modules[e].pairs_price[pair])

    # Unnatural Discrepancy
    if (abs(spot_prices[0][0] - spot_prices[1][0]) / spot_prices[0][0]) > Decimal(1):
        return None

    usd_vals = (uniswap.token_values[pair[0]], uniswap.token_values[pair[1]])
    
    # Calculate Realized value for each exchange

    realized_prices = []
    for i in range(0, len(exchanges)):
        temp_val = (Decimal(0.997) * spot_prices[i][0] * Decimal(0.99) * optimal_size) - (gas_cost / usd_vals[0])
        realized_prices.append(temp_val)

    # Return swap if profit to be made. Else None
    swap = checkSwap(optimal_size, pair, realized_prices, spot_prices, gas_cost)
    if swap is not None:
        print(optimal_size, "of", pair[1], "for", pair[0])
        print(pair, ":", spot_prices)
        return swap
    else:
        return None

def getSwaps(pairs):
    # Get the gas fees
    gas_cost = getGas()
    swaps = []

    # Call getSwap for each pair and return swap if profit
    for pair in pairs:
        res = getSwap(pair, gas_cost)
        if res is not None:
            swaps.append(res)
    
    for swap in swaps:
        printSwap(swap)
        #print("Swap", swap[0], "of", swap[1][1], "for", swap[1][0], "on", swap[2][0], "and sell it on", swap[2][1], ". \n Spead of $", abs(swap[3][0] - swap[3][1]) * uniswap.token_values[swap[1][0]], "/", abs(swap[3][0] - swap[3][1]), swap[1][0])
    return swaps