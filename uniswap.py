import requests
import json
import multiprocessing
from functools import partial


num_processes = multiprocessing.cpu_count()
pairs_id = {}
pairs_info = {}
v3_url = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"

def fillPairs(pairs):
    query = """
    {
        pools(first:10, orderBy:volumeUSD, orderDirection:desc) {
            id
            token0 {
                symbol
                id
            }
            token1 {
                symbol
                id
            }
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
            pairs_id[temp_pair] = (pools[i]['token0']['id'], pools[i]['token1']['id'])

def getPairInfo(pair, pairs_id):
    ids = pairs_id[pair]

    query = f"""
    {{
        pools(first: 1, where: {{
            token0:"{ids[0]}",
            token1:"{ids[1]}"
        }}, orderBy:volumeUSD, orderDirection:desc) {{
            id
            token0 {{
                symbol
                id
                decimals
            }}
            token1 {{
                symbol
                id
                decimals
            }}
            liquidity
            tick
            txCount
            totalValueLockedETH
        }}
    }}
    """
    
    response = json.loads(requests.post(v3_url, json={'query': query}).text)
    pools = response['data']['pools']
    return pools[0]


def updatePairsInfo(pairs):
    pool = multiprocessing.Pool(processes=num_processes)
    partial_func = partial(getPairInfo, pairs_id=pairs_id)
    result = pool.map(partial_func, pairs)
    pool.close()
    pool.join()

    for res, pair in zip(result, pairs):
        pairs_info[pair] = res


# if __name__ == "__main__":
#     # Get the pairs to trade on
#     fillPairs()

#     # Fetch information for given trading pair
#     for pair in pairs:
#         print(pair, ": ", pairs_info[pair]['token0Price'], ",", pairs_info[pair]['token1Price'])

# Calculate price based on the information