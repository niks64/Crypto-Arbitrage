import swaps
import uniswap

pairs = []

def sendSwaps(swaps):
    pass

def updatePairs():
    uniswap.updatePairInfo(pairs)

if __name__ == "__main__":
    # Get the most liquid pairs
    uniswap.fillPairs(pairs)

    # Get the information for these pairs
    updatePairs()



    swaps = swaps.getSwaps()

    sendSwaps(swaps)
