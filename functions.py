from requests import Session, TooManyRedirects
import requests
import threading
import pandas as pd
from web3 import Web3, HTTPProvider
import statistics
from uniswap import Uniswap
from variables import *
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import time
import variables as vars


###########################
##### Instantiators #######
###########################

uniswap_wrapper = Uniswap(vars.metamaskaddress, vars.privatekey, vars.infuraurl, version = 3)
w3 = Web3(HTTPProvider("https://restless-delicate-lake.discover.quiknode.pro/1372d20d14a4f985176e424e61ad6df1e403f8a3/"))
web3_f = w3.eth.contract(address=uniswap_wrapper.address, abi=vars.factoryABI)
client = Client(transport = RequestsHTTPTransport( url = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2', verify=True, retries=3,))
etherscan_api = "https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey=B8MYXAN2HXFZYDYFK1MT8C9WJN4J77U4CD"

###############################
#####Connection Functions######
###############################
def uniswapGraphHTTP():
    sample_transport = RequestsHTTPTransport(
    url = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3',
    #
    verify=True,
    retries=3,
    )
    return sample_transport

def connectUni():
    uniswap_wrapper = Uniswap(vars.metamaskaddress, vars.privatekey, vars.infuraurl, version = 3)

    session = Session()
    session.headers.update(vars.coinheaders)

    try:
        response = session.get(vars.coinurl, params = vars.coinparam).json()
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
def triCalcAbsolute(BaseQuote_CA, BaseQuote_CB, BaseQuote_AB):
    return BaseQuote_CB / BaseQuote_CA - BaseQuote_AB

def triCalcPercent(BaseQuote_CA, BaseQuote_CB, BaseQuote_AB):
    return triCalcAbsolute(BaseQuote_CA, BaseQuote_CB, BaseQuote_AB)/ BaseQuote_AB * 100

#Calculate amount of y received from exchanging n tokens of x
#x is the given currency, y the received currency, k the constant of the pair, and n the number of token x to give
def calcPoolExchange(x, y, k, n):
    return y - k / (x + n)

#Use as such. The denomination value is the difference between the decimals of the base and quote currency. This is because currencies are stored in different decimal points for precision
#print(sqrtToPrice(sqrprice, coindecimals['eth'] - coindecimals['usdc']))
def sqrtToPrice(value, token0dec = 0, token1dec = 0):
    value = int(value)
    #return ((value ** 2) / (2**192)) / (10 ** (token0dec - token1dec))
    return ((value ** 2) / (2**192)) / (10 ** (token1dec - token0dec))
###############################
#####Price/Rate Functions######
###############################
def getInputPrice(token0, token1):
    raw_price = uniswap_wrapper.get_price_input(vars.addrbook[token0], vars.addrbook[token1], 10 ** vars.addrdecimals[token0])
    adjusted_price = raw_price / 10** int(vars.addrdecimals[token1])
    return adjusted_price

#This library always assumes the routing token1 -> (w)eth -> token2 for token -> token transactions (on Uniswap v2) and gets the prices directly
# from the contract (we're not computing prices ourselves here, just asking the contract for the price given a route).
#Different tokens have different decimals, e.g. 6 for USDC and 18 for WETH, leading one token of USDC being worth much more than one unit of WETH in raw data
#Uniswap pairs are ordered so the currency with the lowest address comes
def get_token_price_in_eth(self, owner, weth_address,token):
    weth_address = self.w3.toChecksumAddress(weth_address)#WETH
    erc20_weth = self.erc20_contract(weth_address)
    owner = self.w3.toChecksumAddress(owner)#Uni:Token input exchange ex: UniV2:DAI
    weth_balance: int = erc20_weth.functions.balanceOf(owner).call()
    weth_balance = float(self.w3.fromWei(weth_balance,'ether') )
    print (f'WETH quantity in Uniswap Pool = {weth_balance}')
    token_address = self.w3.toChecksumAddress(token) # Like DAI
    erc20 = self.erc20_contract(token_address)
    token_balance: int = erc20.functions.balanceOf(owner).call()
    gwei = 1000000000
    token_balance = float(token_balance / gwei)
    print (f'Token balance in Uniswap Pool = {token_balance}')
    return float(weth_balance/token_balance)  # price of token

###Subgraph Query Functions###
def run_query(uri, query, statusCode = 200):
    request = requests.post(uri, json={'query': query})
    if request.status_code == statusCode:
        return request.json()
    else:
        raise Exception(f"Unexpected status code returned: {request.status_code}")

def graph_query(query):
    return run_query("https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3", query)


def queryGraph1(query):
    #Note: pass parameter as separate input. If not, unacceptable recursion occurs
    response = client.execute(query)
    pairs = []
    for i in response['pairs']:
        pairs.append([
            i['token0']['symbol'],
            i['token1']['symbol'],
            i['volumeUSD']
        ])

    df = pd.DataFrame(pairs)
    print(df.head())

#Put {{ to make { a literal
def getLastTransaction(pair_id, number = 1):
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
def getPool(pair_id):
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

#Example output
#{'feeTier': '100', 'sqrtPrice': '79229631348333122472707'}
def getPairPrice(pair_id):
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
def etherscanPrice():
    response = requests.get("https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey=B8MYXAN2HXFZYDYFK1MT8C9WJN4J77U4CD")
    return response.json()['result']

#Divide fee by 10,000 to get percentage
def updateGraph(pairs = ['dai-usdc', 'usdc-eth', 'wbtc-eth', 'eth-usdt', 'usdc-usdt', 'frax-usdc', 'usdc-usdm']):
    pair_Graph = {}
    for i in pairs:
        res = getPairPrice(vars.pairbook[i])
        #This cannot be efficient
        #Splits the pair into the names of its currencies
        coins = i.split('-', 1)
        pair_Graph[i] = sqrtToPrice(res['sqrtPrice'], vars.coindecimals[coins[0]], vars.coindecimals[coins[1]])
        #Adjust for Uniswap fee, but not transaction fee
        pair_Graph[i] *= (1 - int(res['feeTier']) / 10000)

    return pair_Graph

#test_Graph = updateGraph()
#print(test_Graph['dai-usdc'])
#print(test_Graph['usdc-eth'])
#print(test_Graph['usdc-usdt'])
#Get transaction recipet
#web3.eth.getTransactionReceipt(transaction_hash)
#print(getPairPrice(vars.pairbook['dai-usdc']))

### Example Usage ###
#gas_prices = estimateGasTest()
#meangas = statistics.mean(gas_prices)
#mediangas = statistics.median(gas_prices)
#print(meangas/10**9)
#print(mediangas/10**18)
#print(w3.eth.getGasPrice())
#max_wait_seconds = 120
#print(getLatestBlockRewardFee(75))
#print(w3.eth.estimate_gas({'to': '0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8', 'from':w3.eth.coinbase, 'value': 12345}))

#estimated_gas = web3_f.functions.withdraw(w3.toWei(0.1, "ether")).estimateGas()
#print(estimated_gas)

#data = getPool('eth', 'usdc', "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8")
#raw_pair = float(data['data']['pool']['volumeToken0'])/ float(data['data']['pool']['volumeToken1'])
#sqrprice = float(data['data']['pool']['sqrtPrice'])

#def get_pair(token0, token1):

#print(calcPoolExchange(5734, 6379363, 5734*6379363, 1))
#print(triCalcAbsolute(1.5028, 1/0.8678, 1/1.3021))
#print(triCalcPercent(1.5028, 1/0.8678, 1/1.3021))

#print(getLastTransaction('0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8'))

#print(sqrtToPrice(sqrtprice, vars.coindecimals['eth'] - vars.coindecimals['usdc']))

#dicte = getPairPrice("0x5777d92f208679db4b9778590fa3cab3ac9e2168")
#print(dicte)
#sqrprice = dicte['sqrtPrice']
#print(sqrprice)
#print(sqrtToPrice(sqrprice))
#print(sqrtToPrice(sqrprice, vars.coindecimals['dai'], vars.coindecimals['usdc']))


#dai-usdc denom 0 1.0000371826615529e-12
#dai-usdc dai dec - usdc dec 1.0000371826615528e-24
#usdc-eth usdc dec - eth dec 5.857938093575771e+22
#usdc-usdt usdc dec - usdt dec 99.95942696264916