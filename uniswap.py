import requests
import json
import multiprocessing
from functools import partial
import decimal


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

def fillTokenValues(pairs):
    toRemove = []
    for pair in pairs:
        ids = pairs_id[pair]
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
        
        # First ID
        data = getResponse(query.format(id=ids[0]))
        if decimal.Decimal(data['token']['derivedETH']) == decimal.Decimal(0):
            toRemove.append(pair)
            continue
        token_values[pair[0]] = decimal.Decimal(data['token']['derivedETH']) * decimal.Decimal(data['bundle']['ethPriceUSD'])
        
        # Second ID
        data = getResponse(query.format(id=ids[1]))
        if decimal.Decimal(data['token']['derivedETH']) == decimal.Decimal(0):
            toRemove.append(pair)
            continue
        token_values[pair[1]] = decimal.Decimal(data['token']['derivedETH']) * decimal.Decimal(data['bundle']['ethPriceUSD'])
    
    for pair in toRemove:
        pairs.remove(pair)

def fillPairs(pairs):
    query = """
    {
        pools(first:50, orderBy:volumeUSD, orderDirection:desc, skip:20) {
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
    pool = multiprocessing.Pool(processes=num_processes)
    partial_func = partial(getPairInfo, pairs_id=pairs_id)
    result = pool.map(partial_func, pairs)
    pool.close()
    pool.join()

    for res, pair in zip(result, pairs):
        pairs_info[pair] = res

def updatePrices(pairs):
    # update the prices array
    for pair in pairs:
        first = decimal.Decimal(pairs_info[pair]['token0Price'])
        second = decimal.Decimal(pairs_info[pair]['token1Price'])
        pairs_price[pair] = (first, second)
    
    # slippage = decimal.Decimal("0.004")
    # price_impact = decimal.Decimal("0.005")
    # for pair in pairs:
        # token0_price = decimal.Decimal(pairs_info[pair]['token0Price'])
        # token1_price = decimal.Decimal(pairs_info[pair]['token1Price'])

    #     token0_price -= (slippage * token0_price + price_impact * token0_price)
    #     token1_price -= (slippage * token1_price + price_impact * token1_price)
    #     pairs_price[pair] = (token0_price, token1_price)


def getActualPrice(pair):
    slippage = 0.005
    price_impact = 0.005

    token0_price = decimal.Decimal(pairs_info[pair]['token0Price'])
    token1_price = decimal.Decimal(pairs_info[pair]['token1Price'])

    token0_price = token0_price * decimal.Decimal(1-slippage)
    token1_price = token1_price * decimal.Decimal(1-slippage)

    token0_price = token0_price * decimal.Decimal(1-price_impact)
    token1_price = token1_price * decimal.Decimal(1-price_impact)

    return (token0_price, token1_price)