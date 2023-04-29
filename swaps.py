import decimal

exchanges = ["uniswap", "sushiswap"]
modules = {
    "uniswap": __import__("uniswap"),
    "sushiswap": __import__("sushiswap")
}

def getSwaps(pairs):
    
    res = []
    return res
    for pair in pairs:
        prices = [0.0] * len(exchanges) 
        for i in range(0, len(exchanges)):
            prices[i] = 0

    return res