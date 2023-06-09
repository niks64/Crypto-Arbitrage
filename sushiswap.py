import requests
import json
import multiprocessing
from functools import partial
import decimal

num_processes = multiprocessing.cpu_count()
pairs_id = {}
pairs_info = {}
pairs_price = {}

url = "https://api.thegraph.com/subgraphs/name/sushiswap/exchange"

def convertSymbolsToName(pair):
    first = pair[0] + "-" + pair[1]
    second = pair[1] + "-" + pair[0]
    res = (first, second)
    return res

def getReponse(query):
    response = json.loads(requests.post(url, json={'query': query}).text)

    try:
        data = response['data']
        return data
    except KeyError:
        return None
    

def fillIds(pairs):
    toRemove = []
    for pair in pairs:
        convertedPair = convertSymbolsToName(pair)
        query = """
        {{
            pairs(where:{{
                or: [
                    {{name: "{}"}},
                    {{name: "{}"}},
                ]
            }} first:1, orderBy:volumeUSD, orderDirection: desc) {{
                id
                token0 {{
                    id
                }}
                token1 {{
                    id
                }}
            }}
        }}
        """.format(convertedPair[0], convertedPair[1])

        data = getReponse(query)
        if data is None:
            #print("SushiSwap: No pairs found for", pair)
            continue
        
        if len(data['pairs']) == 0:
            #print("SushiSwap: No pairs found for", pair)
            toRemove.append(pair)
            continue

        pool = data['pairs'][0]
        pairs_id[pair] = (pool['token0']['id'], pool['token1']['id'])
    
    for pair in toRemove:
        pairs.remove(pair)

def getPairInfo(pair, pairs_id):
    ids = pairs_id[pair]
    query = f"""
    {{
        pairs(where: {{
            token0: "{ids[0]}",
            token1: "{ids[1]}"}}, first: 5, orderBy: volumeUSD, orderDirection: desc) {{
        id
        token0 {{
            id
            symbol
            decimals
        }}
        token1 {{
            id
            symbol
            decimals
        }}
        reserve0
        reserve1
        token0Price
        token1Price
        }}
    }}
    """
    data = getReponse(query)

    if data is None:
        print("Pool not found for:", pair)
        return None
    
    return data['pairs'][0]


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
    first = decimal.Decimal(pairs_info[pair]['token0Price'])
    second = decimal.Decimal(pairs_info[pair]['token1Price'])

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
    #     first = decimal.Decimal(pairs_info[pair]['token0Price'])
    #     second = decimal.Decimal(pairs_info[pair]['token1Price'])
    #     pairs_price[pair] = (first, second)

def getActualPrice(pair, size=1):
    slippage = 0.005
    reserve_0 = decimal.Decimal(pairs_info[pair]['reserve0'])
    reserve_1 = decimal.Decimal(pairs_info[pair]['reserve1'])
    const_product = reserve_0 * reserve_1
    
    # Price impact
    new_price_0 = (const_product / ((reserve_1 + size) ** 2))
    new_price_1 = (const_product / ((reserve_0 + size) ** 2))

    # Slippage
    new_price_0 = new_price_0 * decimal.Decimal(1-slippage)
    new_price_1 = new_price_1 * decimal.Decimal(1-slippage)

    # Transaction fees


    return (new_price_0, new_price_1)

