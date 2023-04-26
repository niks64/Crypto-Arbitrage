import requests
import json
# Calculate price based on the information


pairs = []
pairs_info = {}
v3_url = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"

def fillPairs():
    query = """
    {
        pools(first:10, orderBy:volumeUSD, orderDirection:desc) {
            id
            token0 {
                name
                symbol
                id
                decimals
                volumeUSD
            }
            token1 {
                name
                symbol
                id
                decimals
                volumeUSD
            }
            token0Price
            token1Price
        }
    }
    """
    
    # Get the pools with the highest liquidity
    response = json.loads(requests.post(v3_url, json={'query': query}).text)
    pools = response['data']['pools']

    # Add the pairs from the pools to the list
    for i in range (0, len(pools)):
        temp_pair = (pools[i]['token0']['symbol'], pools[i]['token1']['symbol'])
        if temp_pair not in pairs:
            pairs.append(temp_pair)
            pairs_info[temp_pair] = pools[i]


if __name__ == "__main__":
    # Get the pairs to trade on
    fillPairs()

    # Fetch information for given trading pair
    for pair in pairs:
        print(pair, ": ", pairs_info[pair]['token0Price'], ",", pairs_info[pair]['token1Price'])