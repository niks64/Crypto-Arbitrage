import requests
import json

# Fetch information for given trading pair
# Calculate price based on the information


pairs = []
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
            totalValueLockedETH
        }
        }
    """
    response = json.loads(requests.post(v3_url, json={'query': query}).text)
    pools = response['data']['pools']
    for i in range (0, len(pools)):
        temp_pair = (pools[i]['token0']['symbol'], pools[i]['token1']['symbol'])
        if temp_pair not in pairs:
            pairs.append(temp_pair)

if __name__ == "__main__":
    fillPairs()
    print(pairs)