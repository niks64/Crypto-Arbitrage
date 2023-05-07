import requests
import json
import multiprocessing
from functools import partial
from decimal import Decimal

# Code for uniswap 


num_processes = multiprocessing.cpu_count()
pairs_id = {}
pairs_info = {}
pairs_price = {}
token_values = {}
v3_url = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"

def getResponse(query):
    response = json.loads(requests.post(v3_url, json={'query': query}).text)

    try:
        data = response['data']
        return data
    except KeyError:
        return None

def fillTokenValue(pair, pairs_id):
    pair_id = pairs_id[pair]
    query = """
    {{
        token(id: "{id}") {{
            derivedETH
        }}
        bundle(id: "1") {{
            ethPriceUSD
        }}
    }}
    """
    data = getResponse(query.format(id=pair_id[0]))
    if data is None:
        return (Decimal(0), Decimal(0))
    first = Decimal(data['token']['derivedETH']) * Decimal(data['bundle']['ethPriceUSD'])

    data = getResponse(query.format(id=pair_id[1]))
    if data is None:
        return (Decimal(0), Decimal(0))
    second = Decimal(data['token']['derivedETH']) * Decimal(data['bundle']['ethPriceUSD'])

    return (first, second)


def fillTokenValues(pairs):
    toRemove = []

    pool = multiprocessing.Pool(processes=num_processes)
    partial_func = partial(fillTokenValue, pairs_id=pairs_id)
    result = pool.map(partial_func, pairs)
    pool.close()
    pool.join()

    for res, pair in zip(result, pairs):
        if res[0] == Decimal(0) or res[1] == Decimal(0):
            toRemove.append(pair)
            continue
        token_values[pair[0]] = res[0]
        token_values[pair[1]] = res[1]
    
    for pair in toRemove:
        pairs.remove(pair)

def fillPairs(pairs):
    query = """
    {
        pools(first:1000, orderBy:volumeUSD, orderDirection:desc, skip:1000) {
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
    data = getResponse(query)
    if data is None:
        print("fillPairs() failed. Retrying...")
        fillPairs(pairs)
        return
    
    pools = data['pools']

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
            }}
            token1 {{
                symbol
                id
            }}
            token0Price
            token1Price
        }}
    }}
    """
    data = getResponse(query)
    if data is None:
        print("Pool not found for:", pair)
        return None
    
    return data['pools'][0]


def updatePairsInfo(pairs):
    toRemove = []
    pool = multiprocessing.Pool(processes=num_processes)
    partial_func = partial(getPairInfo, pairs_id=pairs_id)
    result = pool.map(partial_func, pairs)
    pool.close()
    pool.join()

    for res, pair in zip(result, pairs):
        if res is None:
            toRemove.append(pair)
            continue
        pairs_info[pair] = res

    for pair in toRemove:
        pairs.remove(pair)

def updatePrice(pair, pairs_info):
    first = Decimal(pairs_info[pair]['token0Price'])
    second = Decimal(pairs_info[pair]['token1Price'])

    return (first, second)

def updatePrices(pairs):
    # update the prices array
    pool = multiprocessing.Pool(processes=num_processes)
    partial_func = partial(updatePrice, pairs_info=pairs_info)
    result = pool.map(partial_func, pairs)
    pool.close()
    pool.join()

    for res, pair in zip(result, pairs):
        pairs_price[pair] = res

    # for pair in pairs:
    #     first = Decimal(pairs_info[pair]['token0Price'])
    #     second = Decimal(pairs_info[pair]['token1Price'])
    #     pairs_price[pair] = (first, second)


def getActualPrice(pair):
    slippage = 0.005
    price_impact = 0.005

    token0_price = Decimal(pairs_info[pair]['token0Price'])
    token1_price = Decimal(pairs_info[pair]['token1Price'])

    token0_price = token0_price * Decimal(1-slippage)
    token1_price = token1_price * Decimal(1-slippage)

    token0_price = token0_price * Decimal(1-price_impact)
    token1_price = token1_price * Decimal(1-price_impact)

    return (token0_price, token1_price)