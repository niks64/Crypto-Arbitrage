import swaps
import uniswap
import sushiswap
import time

pairs = []

def fillIds():
    sushiswap.fillIds(pairs)

def sendSwap(swap):
    pass

def updatePairsInfo():
    uniswap.updatePairsInfo(pairs)
    sushiswap.updatePairsInfo(pairs)

def updatePrices():
    uniswap.updatePrices(pairs)
    sushiswap.updatePrices(pairs)

if __name__ == "__main__":


    init_start = time.perf_counter()

    # Get the most liquid pairs
    uniswap.fillPairs(pairs)

    # Fill the ids for the pairs
    fillIds()
    # for pair in pairs:
    #     print(pair, ":", sushiswap.pairs_id[pair])

    init_end = time.perf_counter()
    elapsed_time = init_end - init_start


    print(f"Intialization Phase: {elapsed_time: .2f} seconds")

    update_start = time.perf_counter()
    
    # Get the information for these pairs
    updatePairsInfo()

    # Update the prices
    updatePrices()
    
    # Get the token prices in USD
    uniswap.fillTokenValues(pairs)

    update_end = time.perf_counter()
    elapsed_time = update_end - update_start
    print(f"Update Phase: {elapsed_time: .2f} seconds")


    detect_start = time.perf_counter()
    
    swaps = swaps.getSwaps(pairs)
    if len(swaps) != 0: sendSwap(swaps[0])
    
    detect_end = time.perf_counter()
    elapsed_time = detect_end - detect_start
    print(f"Detect Phase: {elapsed_time: .2f} seconds")
    
