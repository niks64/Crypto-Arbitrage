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

def getGas():
    eth = Etherscan(etherscan_api_key)
    gas_oracle = eth.get_gas_oracle()
    return min(Decimal(15),Decimal(gas_oracle["SafeGasPrice"]))

def checkSwap(prices):
    uniswap_price = prices[0][0]
    sushiswap_price = prices[1][0]

    if (Decimal(abs(uniswap_price - sushiswap_price)) / (uniswap_price)) > Decimal(0.01):
        return True

    return False

def getSwap(pair, gas_cost):

    # Get the optimum size for the transaction
    reserve_0 = Decimal(sushiswap.pairs_info[pair]['reserve0'])
    reserve_1 = Decimal(sushiswap.pairs_info[pair]['reserve1'])
    optimum_size = (Decimal(math.sqrt(gas_cost)) * reserve_1) / (Decimal(math.sqrt(reserve_0 * Decimal(uniswap.token_values[pair[0]]))) - Decimal(math.sqrt(gas_cost)))
    if optimum_size < Decimal(0):
        return None

    # Calculate spot value and realized value for each exchange
    spot_prices = []
    for e in exchanges:
        spot_prices.append(modules[e].pairs_price[pair])
    
    usd_vals = (uniswap.token_values[pair[0]], uniswap.token_values[pair[1]])

    realized_prices = []
    for i in range(0, len(exchanges)):
        temp_val = usd_vals[0] * Decimal(0.997) * spot_prices[i][0] * Decimal(0.98) * optimum_size - gas_cost
        realized_prices.append((temp_val, Decimal(1)/temp_val))
        
    # Return swap if profit to be made. Else None
    print(pair, ":", realized_prices)
    if checkSwap(realized_prices):
        if realized_prices[0][0] < realized_prices[1][0]:
            first = "uniswap"
            second = "sushiswap"
        else:
            first = "sushiswap"
            second = "uniswap"
        return (optimum_size, pair, first, second, realized_prices)
    
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
        print("Buy", swap[0], "of", swap[1][0], "on", swap[2], "and sell the resulting", swap[1][1], "on", swap[3])
    return swaps