import swaps
import uniswap

pairs = []

def sendSwaps(swaps):
    pass

def updatePairsInfo():
    uniswap.updatePairsInfo(pairs)

if __name__ == "__main__":
    # Get the most liquid pairs
    uniswap.fillPairs(pairs)

    # Get the information for these pairs
    updatePairsInfo()

    for pair in pairs:
        print(uniswap.pairs_info[pair])
        print()


    swaps = swaps.getSwaps()

    sendSwaps(swaps)
