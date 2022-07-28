from requests import Session, TooManyRedirects
import requests
import threading
from web3 import Web3, HTTPProvider
import statistics
from uniswap import Uniswap
from variables import *
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import time


##########################
##### Instantiators ######
##########################

uniswap_wrapper = Uniswap(vars.metamaskaddress, vars.privatekey, vars.infuraurl, version = 3)
w3 = Web3(HTTPProvider("https://restless-delicate-lake.discover.quiknode.pro/1372d20d14a4f985176e424e61ad6df1e403f8a3/"))
web3_f = w3.eth.contract(address=uniswap_wrapper.address, abi=factoryABI)
client = Client(transport = RequestsHTTPTransport( url = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2', verify=True, retries=3,))

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

#This library always assumes the routing token1 -> (w)eth -> token2 for token -> token transactions (on Uniswap v2) and gets the prices directly
# from the contract (we're not computing prices ourselves here, just asking the contract for the price given a route).
#Different tokens have different decimals, e.g. 6 for USDC and 18 for WETH, leading one token of USDC being worth much more than one unit of WETH in raw data
#Uniswap pairs are ordered so the currency with the lowest address comes

###############################
#####Price/Rate Functions######
###############################
def getInputPrice(token0, token1):
    raw_price = uniswap_wrapper.get_price_input(vars.addrbook[token0], vars.addrbook[token1], 10 ** vars.addrdecimals[token0])
    adjusted_price = raw_price / 10** int(vars.addrdecimals[token1])
    return adjusted_price

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

#raw values are in gwei or something that multiplies it by huge number
def sqrtToPrice(value, denom = 0):
    return ((value ** 2) / (2**192)) / (10 ** denom)

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
def getPool(token0, token1, pair_id):
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


### Example Usage ###
gas_prices = estimateGasTest()
meangas = statistics.mean(gas_prices)
mediangas = statistics.median(gas_prices)
print(meangas/10**9)
print(mediangas/10**18)

max_wait_seconds = 120
print(getLatestBlockRewardFee(75))
#print(w3.eth.estimate_gas({'to': '0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8', 'from':w3.eth.coinbase, 'value': 12345}))

#estimated_gas = web3_f.functions.withdraw(w3.toWei(0.1, "ether")).estimateGas()
#print(estimated_gas)

#data = getPool('eth', 'usdc', "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8")
#raw_pair = float(data['data']['pool']['volumeToken0'])/ float(data['data']['pool']['volumeToken1'])
#sqrprice = float(data['data']['pool']['sqrtPrice'])
#print(sqrtToPrice(sqrprice, coindecimals['eth'] - coindecimals['usdc']))
#def get_pair(token0, token1):

#print(calcPoolExchange(5734, 6379363, 5734*6379363, 1))
#print(triCalcAbsolute(1.5028, 1/0.8678, 1/1.3021))
#print(triCalcPercent(1.5028, 1/0.8678, 1/1.3021))

#print(getLastTransaction('0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8'))

#print(sqrtToPrice(sqrtprice, vars.coindecimals['eth'] - vars.coindecimals['usdc']))
