import json
from numpy import Infinity
from requests import Session, TooManyRedirects
import requests
from web3 import Web3, HTTPProvider
from uniswap import Uniswap
from gql.transport.requests import RequestsHTTPTransport
import time
import variables as v
import math



###########################
##### Instantiators #######
###########################

uniswap_wrapper = Uniswap(v.metamaskaddress, v.privatekey, v.infuraurl, version = 3)
w3 = Web3(HTTPProvider("https://restless-delicate-lake.discover.quiknode.pro/1372d20d14a4f985176e424e61ad6df1e403f8a3/"))
web3_f = w3.eth.contract(address=uniswap_wrapper.address, abi=v.factoryABI)
etherscan_api = "https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey=B8MYXAN2HXFZYDYFK1MT8C9WJN4J77U4CD"

###############################
#####Connection Functions######
###############################
def uniswapGraphHTTP() -> RequestsHTTPTransport:
    sample_transport = RequestsHTTPTransport(
    url = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3',
    #
    verify=True,
    retries=3,
    )
    return sample_transport

def connectUni():
    uniswap_wrapper = Uniswap(v.metamaskaddress, v.privatekey, v.infuraurl, version = 3)

    session = Session()
    session.headers.update(v.coinheaders)

    try:
        response = session.get(v.coinurl, params = v.coinparam).json()
        data = response['data']
        ethdata = data['ETH']
        pricedata = ethdata['quote']
        usdprice = pricedata['USD']
        ethprice = usdprice['price']

    except (ConnectionError, time.Timeout, TooManyRedirects) as e:
        print(e)

################################
#####Calculation Functions######
################################

#calculates the theoretical profit from arbritage trade
#NOTE: Convention is base/quote. E.g. EUR/USD = 1.3 means selling 1 base EUR gives 1.3 USD, and with 1 EUR you buy 1.3 USD
#Standardise by setting currency C as the base
#Functions calculate absolute and percent disparity between indirect and direct currency pairs
#A positive value indicates profit on path (trade CB -> BA -> AC), a negative indicates (trade CA -> AB -> AC)
def triCalcAbsolute(BaseQuote_CA, BaseQuote_CB, BaseQuote_AB) -> float:
    return BaseQuote_CB / BaseQuote_CA - BaseQuote_AB

def triCalcPercent(BaseQuote_CA, BaseQuote_CB, BaseQuote_AB) -> float:
    return triCalcAbsolute(BaseQuote_CA, BaseQuote_CB, BaseQuote_AB)/ BaseQuote_AB * 100
    
def triCalcMulti(AB, BC, CA):
    return AB*BC*CA - 1

def triCalcMultiPercent(AB, CB, CA):
    return triCalcMulti(AB, CB, CA) * 100

#Calculate amount of y received from exchanging n tokens of x
#x is the given currency, y the received currency, k the constant of the pair, and n the number of token x to give
def calcPoolExchange(x, y, k, n) -> float:
    return y - k / (x + n)

#Use as such. The denomination value is the difference between the decimals of the base and quote currency. This is because currencies are stored in different decimal points for precision
#print(sqrtToPrice(sqrprice, coindecimals['eth'] - coindecimals['usdc']))
def sqrtToPrice(value, token0dec = 0, token1dec = 0) -> float:
    value = int(value)
    #return ((value ** 2) / (2**192)) / (10 ** (token0dec - token1dec))
    return ((value ** 2) / (2**192)) / (10 ** (token1dec - token0dec))

###############################
#####Price/Rate Functions######
###############################
def getInputPrice(token0, token1) -> float:
    raw_price = uniswap_wrapper.get_price_input(v.addrbook[token0], v.addrbook[token1], 10 ** v.addrdecimals[token0])
    adjusted_price = raw_price / 10** int(v.addrdecimals[token1])
    return adjusted_price

###Subgraph Query Functions###
#Runs a subgraph query for a subgraph uri and query
def run_query(uri : str, query : str, statusCode = 200) -> json:
    request = requests.post(uri, json={'query': query})
    if request.status_code == statusCode:
        return request.json()
    else:
        raise Exception(f"Unexpected status code returned: {request.status_code}")

#Runs an arbitrary subgraph query on the uniswap v3 subgraph
def graph_query(query : str) -> json:
    return run_query("https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3", query)

#Put {{ to make { a literal
def getLastTransaction(pair_id, number = 1) -> json:
    query = f'''
        {{
        swaps(first: {number},orderBy: timestamp, orderDirection: desc, where:
        {{ pool: "{pair_id}" }}
        ) {{
        pool {{
            token0 {{
            symbol
            }}
            token1 {{
            symbol
            }}
        }}
        amount0
        amount1
        }}
        }}
    '''
    response = graph_query(query)
    return response;

#sqrtprice = int(response['data']['pool']['sqrtPrice'])
#{'data': {'pool': {'token0': {'symbol': 'DAI'}, 'token1': {'symbol': 'USDC'}, 'tick': '-276324', 'feeTier': '100', 'sqrtPrice': '79229630437327735417221', 'liquidity': '5120286464337725966312757', 'volumeToken0': '9892392969.019477464883758349', 'volumeToken1': '9892527261.516269'}}}
def getPool(pair_id) -> json:
    query = f'''
    {{
    pool(id: "{pair_id}") {{
    token0{{
        symbol
    }}
    token1{{
        symbol
    }}
    tick
    feeTier
    sqrtPrice
    liquidity
    volumeToken0
    volumeToken1
    }}
    }}
    '''
    response = graph_query(query)
    return response;

#Input is the nth biggest pools by volume, sorted in descending order
#Returns a list of dictionaries that has keys the same as the query request. dict example
#{'token0': {'symbol': '100MD'}, 'token1': {'symbol': 'SHIB'}, 'feeTier': '3000', 'sqrtPrice': '27679464853141944727867160'}
def getPoolFast(number = 10) -> list[dict]:
    query = f'''
    {{
    pools(first: {number}, orderBy: volumeUSD, orderDirection: desc) {{
    token0{{
        symbol
    }}
    token1{{
        symbol
    }}
    feeTier
    sqrtPrice
    }}
    }}
    '''
    response = graph_query(query)
    return response['data']['pools'];

#Example output
#{'feeTier': '100', 'sqrtPrice': '79229631348333122472707'}
def getPairPrice(pair_id) -> json:
    query = f'''
    {{
    pool(id: "{pair_id}") {{
    feeTier
    sqrtPrice
    }}
    }}
    '''
    response = graph_query(query)
    return response['data']['pool'];

###web3 Library Functions###
def estimateGasTest():
    pending_transactions = w3.provider.make_request("parity_pendingTransactions", [])
    gas_prices = []
    gases = []
    for tx in pending_transactions["result"[:10]]:
        gas_prices.append(int((tx["gasPrice"]),16))
    return gas_prices

#gets the reward fees of the latest ETH block, parameter in percentiles
def getLatestBlockRewardFee(centile = 0):
    dictlist = w3.eth.fee_history(1, "latest", reward_percentiles=[centile])
    return dictlist['reward'][0]

#Gets the average gas fees from etherscan in gwei. NOTE: This is the average on ETH and not specific to uniswap. Returns a dict with the following key-value pairs (with example data)
#{'LastBlock': '15244511', 'SafeGasPrice': '28', 'ProposeGasPrice': '29', 'FastGasPrice': '30', 'suggestBaseFee': '27.954900621', 'gasUsedRatio': '0.999947884224388,0.999508399524786,0.999793598249169,0.657947983434502,0.183528466489892'}
def etherscanPrice() ->  json:
    response = requests.get("https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey=B8MYXAN2HXFZYDYFK1MT8C9WJN4J77U4CD")
    return response.json()['result']

#Divide fee by 10,000 to get percentage
def updateGraph(pairs = ['dai-usdc', 'usdc-eth', 'wbtc-eth', 'eth-usdt', 'usdc-usdt', 'frax-usdc', 'usdc-usdm']):
    pair_Graph = {}
    for i in pairs:
        res = getPairPrice(v.pairbook[i])
        #This cannot be efficient
        #Splits the pair into the names of its currencies
        coins = i.split('-', 1)
        pair_Graph[i] = sqrtToPrice(res['sqrtPrice'], v.coindecimals[coins[0]], v.coindecimals[coins[1]])
        #Adjust for Uniswap fee, but not transaction fee
        pair_Graph[i] *= (1 - int(res['feeTier']) / 10000)
    return pair_Graph

#Creates an adjacency matrix using dictonary
#coinslist = ['dai', 'usdc', 'wbtc', 'usdt', 'frax', 'usdm', 'eth'], pairslist = ['dai-usdc', 'usdc-eth', 'wbtc-eth', 'eth-usdt', 'usdc-usdt', 'frax-usdc', 'usdc-usdm']
def updatePriceGraph(numberOfPools = 10) -> dict[dict]:
    adj_Matrix = {}
    pools = getPoolFast(numberOfPools)

    for pool in pools:
        adj_Matrix[pool['token0']['symbol']] = {}
        adj_Matrix[pool['token1']['symbol']] = {}

    #Each element pool in pools is a pool stored as a dictionary containing the 2 token names, fee tier and price as raw sqrt form
    for pool in pools:
        #Create line in matrix for the base token
        token0 = pool['token0']['symbol']
        token1 = pool['token1']['symbol']
        rate01 = ( sqrtToPrice(pool['sqrtPrice'], v.coindecimals[token0], v.coindecimals[token1]) ) 
        adj_Matrix[token0][token1] = rate01 * (1 - int(pool['feeTier']) / 10000) 
        #adj_Matrix[token1].update({ token0 : ( sqrtToPrice(pool['sqrtPrice'], v.coindecimals[token1], v.coindecimals[token0]) ) * (1 - int(pool['feeTier']) / 10000) })
        adj_Matrix[token1].update({ token0 : ( 1 / rate01 ) * (1 - int(pool['feeTier']) / 10000) })

    return adj_Matrix

def log_Graph(pair_Graph: dict[dict]):
    for key0 in pair_Graph.keys():
        for key1 in pair_Graph[key0].keys():
            pair_Graph[key0][key1] = -1 * math.log(pair_Graph[key0][key1])

    return pair_Graph

#======= STILL IN TESTING ========#

def find_Arbitrage_Tri(base : str = 'NIL', pair_Graph : dict[dict] = {}, margin : float = 0.3):
    key_list = list(pair_Graph.keys())
    
    #Part of function to specify source currency
    if(base == 'NIL'):
        base = key_list[0]

    for coinA in key_list:
        for coinB in pair_Graph[coinA].keys():
            for coinC in pair_Graph[coinB].keys():
                if coinC in pair_Graph[coinA]:
                    #AB, BC, CA
                    difference = triCalcMultiPercent(pair_Graph[coinA][coinB], pair_Graph[coinB][coinC], pair_Graph[coinC][coinA])

                    if difference > margin:
                        print("Arbitrage found with difference: " + str(difference))
                        print("Coins are " + str(coinA) + " -> " + coinB + " -> " + coinC)
                        print("Rates are " + str(pair_Graph[coinA][coinB]) + " " + str(pair_Graph[coinB][coinC]) + " " + str(pair_Graph[coinC][coinA]))
                        print("\n")
                        return [coinA, coinB, coinC]


def find_Arbitrage_Circular(base_currency : str, pair_Graph : dict[dict]):

    #Generate traversal order with base currency at the start
    key_list = list(pair_Graph.keys())
    vertices = len(key_list)
    
    i = 0
    prev = {}
    while i < len(key_list):
        prev[key_list[i]] = ""
        if(key_list[i] == base_currency):
            holder = key_list[0]
            key_list[0] = key_list[i]
            key_list[i] = holder
        i += 1
    prev[base_currency] = base_currency
    #dictionary of int storing shortest known distance
    min_distance = {}
    #Initialise all distances from base currency to zero
    for i in key_list:
        min_distance[i] = Infinity
    #Initialise the distance from the first element (key stored as first element in key_list) to 0
    min_distance[key_list[0]] = 0

    #dictionary of arrays, containing the shortest path to each array from the base currency
    route_list = {}
    for vertex0 in key_list:
        route_list[vertex0] = [base_currency]



    #Log the distances
    pair_Graph = log_Graph(pair_Graph)
    for x in range (vertices - 1):
        for vertex0 in key_list:
            for vertex1 in pair_Graph[vertex0].keys():
                #print(pair_Graph[vertex0][vertex1])
                #print(str(vertex0) + " " + str(min_distance[vertex0]) + " " + str(vertex1) + " " + str(min_distance[vertex1]) + " " + str(pair_Graph[vertex0][vertex1] + min_distance[vertex0]))
                if(min_distance[vertex1] > pair_Graph[vertex0][vertex1] + min_distance[vertex0]): 
                    min_distance[vertex1] = pair_Graph[vertex0][vertex1] + min_distance[vertex0]

                    #Append vertex1 to vertex0's route and assign to vertex1
                    #route_holder = route_list[vertex0].append(vertex1)
                    #route_list[vertex1] = route_holder
                    prev[vertex1] = vertex0

    #Find negative weight cycles
    print(min_distance)
    for vertex0 in key_list:
        for vertex1 in pair_Graph[vertex0].keys():

            #Find if the shortest distance to vertex0 from base_currency is greater than if going from vertex0 to vertex1
            if(min_distance[vertex1] > pair_Graph[vertex0][vertex1] + min_distance[vertex0]):
                print("Arbitrage found")
                vertex0copy = vertex0
                coin_cycle = [vertex1, vertex0copy]
                print(prev)
                while prev[vertex0copy] not in coin_cycle:
                    coin_cycle.append(prev[vertex0copy])
                    vertex0copy = prev[vertex0copy]
                coin_cycle.append(prev[vertex0copy])
                print("->".join(p for p in coin_cycle[::-1]))
                print("coin cycle is: " + str(coin_cycle) + "\n")

#testgraph = {'USDC': {'WETH': 0.1, 'USDT': 0.9898178173753199, 'WBTC': 1.6}, 'WETH': {'USDC': 10, 'USDT': 1248.3625877632899, 'WBTC': 9.430370805533799e+20, 'DAI': 0.000392296883686367}, 'USDT': {'WETH': 1.2483625877632897e-21, 'USDC': 0.9898178173753199}, 'WBTC': {'WETH': 9.430370805533798, 'USDC': 16831.181464919468}, 'DAI': {'WETH': 0.000392296883686367}}
#testgraph = {'EUR' : {'USD' : 1.111, 'GBP' : 1.2, 'JPY' : 995}, 'USD' : { 'GBP' : 0.909,  'EUR' : 0.9}, 'GBP' : { 'EUR' : 0.8333, 'USD' : 1.1, 'JPY' : 1000}, 'JPY' : {'EUR' : 0.001005, 'GBP' : 0.001}} 
#testgraph = {'EUR' : {'USD' : 1.1586, 'GBP' : 1.4600}, 'USD' : { 'GBP' : 1.6939,  'EUR' : 0.8631106507854307}, 'GBP' : { 'EUR' : 0.68493, 'USD' : 0.59035}} 
testgraph = updatePriceGraph()
print(testgraph)
find_Arbitrage_Tri('WETH', testgraph)
