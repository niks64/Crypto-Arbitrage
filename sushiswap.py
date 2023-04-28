import requests
import json
import multiprocessing

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
            print("No pools found for", pair)
            continue
        
        pool = data['pairs'][0]
        pairs_id[pair] = (pool['token0']['id'], pool['token1']['id'])

def getPairInfo(pair):
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
        print("Retrying...")
        return getPairInfo(pair)
    
    return data['pairs'][0]

def updatePairsInfo(pairs):
    for pair in pairs:
        res = getPairInfo(pair)
        pairs_info[pair] = res

def updatePrices(pairs):
    pass