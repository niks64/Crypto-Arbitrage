import requests
import json
import multiprocessing
from functools import partial
from decimal import Decimal

num_processes = multiprocessing.cpu_count()
pairs_id = {}
pairs_info = {}
token_values = {}
url = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"


def getResponse(query):
    response = json.loads(requests.post(url, json={'query': query}).text)

    try:
        data = response['data']
        return data
    except KeyError:
        return None

def checkPair(pair):
    # Check whether each token in the pair (tuple of tokens) is one word
    for token in pair:
        if " " in token:
            return False
    return True

def fillEthUsd():
    query = """
    {
        bundle(id: "1") {
            ethPrice
        }
    }
    """

    data = getResponse(query)
    if data is None:
        print("Uniswap v2: No eth price found")
        return

    global eth_usd
    eth_usd = Decimal(data['bundle']['ethPrice'])


def fillPairs(pairs):
    print("Enter the number of pairs to fill: ")
    numFirst = int(input())
    print("Enter the number of pairs to skip: ")
    numSkip = int(input())

    # Uniswap v2 subgraph query of most liquid numFirst pairs after skipping numSkip pairs
    query = """
    {{
        pairs(first: {first}, skip: {skip}, orderBy: volumeUSD, orderDirection: desc) {{
            token0 {{
                symbol
                id
            }}
            token1 {{
                symbol
                id
            }}
        }}
    }}
    """.format(first=numFirst, skip=numSkip)

    data = getResponse(query)
    if data is None:
        print("Uniswap v2: No pairs found")
        return
    
    for pair in data['pairs']:
        temp_pair = (pair['token0']['symbol'], pair['token1']['symbol'])
        if temp_pair not in pairs and checkPair(temp_pair):
            pairs.append(temp_pair)
            pairs_id[temp_pair] = (pair['token0']['id'], pair['token1']['id'])        


def getPairInfo(pair):
    ids = pairs_id[pair]

    # query for uniswap v2 subgraph using pair ids
    query = """
    {{
        pairs(
            where: {{
                token0: "{first}", token1: "{second}"
            }}
        ) {{
            reserve0
            reserve1
            token0Price
            token1Price
        }}
    }}
    """.format(first=ids[0], second = ids[1])

    data = getResponse(query)
    if data is None:
        print("Uniswap v2: No data found for", pair)
        return
    
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


def fillTokenValues(pairs):
    pass

def getPrice(pair):
    info = pairs_info[pair]
    if info['token0Price'] == '0' or info['token1Price'] == '0':
        return (Decimal(0), Decimal(0))
    return (Decimal(info['token0Price']), Decimal(info['token1Price']))

