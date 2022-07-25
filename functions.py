import requests
import threading
from web3 import Web3, HTTPProvider
import statistics
from uniswap import Uniswap

#WARNING: Private wallet info, added for testing, do not release
metamaskaddress = "0xF1BC081d62009F4282B639caDa5BC59d3904e12A"
privatekey = "41b9728fe2f9dcc925e7de5538ce503001c8f911c4d1f57223fccaa6616aa0bf"
infuraurl = "https://mainnet.infura.io/v3/4035a313139b4ff2808f4d19c4b5ef61"
coinheaders = {
    'Accepts' : 'application/json',
    'X-CMC_PRO_API_KEY' : '2c234027-2f3e-4ca0-a8d0-1a1b36849365',
}

factoryABI = '''
[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"int24","name":"tickLower","type":"int24"},{"indexed":true,"internalType":"int24","name":"tickUpper","type":"int24"},{"indexed":false,"internalType":"uint128","name":"amount","type":"uint128"},{"indexed":false,"internalType":"uint256","name":"amount0","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount1","type":"uint256"}],"name":"Burn","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":false,"internalType":"address","name":"recipient","type":"address"},{"indexed":true,"internalType":"int24","name":"tickLower","type":"int24"},{"indexed":true,"internalType":"int24","name":"tickUpper","type":"int24"},{"indexed":false,"internalType":"uint128","name":"amount0","type":"uint128"},{"indexed":false,"internalType":"uint128","name":"amount1","type":"uint128"}],"name":"Collect","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":true,"internalType":"address","name":"recipient","type":"address"},{"indexed":false,"internalType":"uint128","name":"amount0","type":"uint128"},{"indexed":false,"internalType":"uint128","name":"amount1","type":"uint128"}],"name":"CollectProtocol","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":true,"internalType":"address","name":"recipient","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount0","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount1","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"paid0","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"paid1","type":"uint256"}],"name":"Flash","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint16","name":"observationCardinalityNextOld","type":"uint16"},{"indexed":false,"internalType":"uint16","name":"observationCardinalityNextNew","type":"uint16"}],"name":"IncreaseObservationCardinalityNext","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"indexed":false,"internalType":"int24","name":"tick","type":"int24"}],"name":"Initialize","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"sender","type":"address"},{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"int24","name":"tickLower","type":"int24"},{"indexed":true,"internalType":"int24","name":"tickUpper","type":"int24"},{"indexed":false,"internalType":"uint128","name":"amount","type":"uint128"},{"indexed":false,"internalType":"uint256","name":"amount0","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"amount1","type":"uint256"}],"name":"Mint","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint8","name":"feeProtocol0Old","type":"uint8"},{"indexed":false,"internalType":"uint8","name":"feeProtocol1Old","type":"uint8"},{"indexed":false,"internalType":"uint8","name":"feeProtocol0New","type":"uint8"},{"indexed":false,"internalType":"uint8","name":"feeProtocol1New","type":"uint8"}],"name":"SetFeeProtocol","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":true,"internalType":"address","name":"recipient","type":"address"},{"indexed":false,"internalType":"int256","name":"amount0","type":"int256"},{"indexed":false,"internalType":"int256","name":"amount1","type":"int256"},{"indexed":false,"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"indexed":false,"internalType":"uint128","name":"liquidity","type":"uint128"},{"indexed":false,"internalType":"int24","name":"tick","type":"int24"}],"name":"Swap","type":"event"},{"inputs":[{"internalType":"int24","name":"tickLower","type":"int24"},{"internalType":"int24","name":"tickUpper","type":"int24"},{"internalType":"uint128","name":"amount","type":"uint128"}],"name":"burn","outputs":[{"internalType":"uint256","name":"amount0","type":"uint256"},{"internalType":"uint256","name":"amount1","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"int24","name":"tickLower","type":"int24"},{"internalType":"int24","name":"tickUpper","type":"int24"},{"internalType":"uint128","name":"amount0Requested","type":"uint128"},{"internalType":"uint128","name":"amount1Requested","type":"uint128"}],"name":"collect","outputs":[{"internalType":"uint128","name":"amount0","type":"uint128"},{"internalType":"uint128","name":"amount1","type":"uint128"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint128","name":"amount0Requested","type":"uint128"},{"internalType":"uint128","name":"amount1Requested","type":"uint128"}],"name":"collectProtocol","outputs":[{"internalType":"uint128","name":"amount0","type":"uint128"},{"internalType":"uint128","name":"amount1","type":"uint128"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"fee","outputs":[{"internalType":"uint24","name":"","type":"uint24"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"feeGrowthGlobal0X128","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"feeGrowthGlobal1X128","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"amount0","type":"uint256"},{"internalType":"uint256","name":"amount1","type":"uint256"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"flash","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"}],"name":"increaseObservationCardinalityNext","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"}],"name":"initialize","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"liquidity","outputs":[{"internalType":"uint128","name":"","type":"uint128"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"maxLiquidityPerTick","outputs":[{"internalType":"uint128","name":"","type":"uint128"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"int24","name":"tickLower","type":"int24"},{"internalType":"int24","name":"tickUpper","type":"int24"},{"internalType":"uint128","name":"amount","type":"uint128"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"mint","outputs":[{"internalType":"uint256","name":"amount0","type":"uint256"},{"internalType":"uint256","name":"amount1","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"observations","outputs":[{"internalType":"uint32","name":"blockTimestamp","type":"uint32"},{"internalType":"int56","name":"tickCumulative","type":"int56"},{"internalType":"uint160","name":"secondsPerLiquidityCumulativeX128","type":"uint160"},{"internalType":"bool","name":"initialized","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint32[]","name":"secondsAgos","type":"uint32[]"}],"name":"observe","outputs":[{"internalType":"int56[]","name":"tickCumulatives","type":"int56[]"},{"internalType":"uint160[]","name":"secondsPerLiquidityCumulativeX128s","type":"uint160[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"name":"positions","outputs":[{"internalType":"uint128","name":"liquidity","type":"uint128"},{"internalType":"uint256","name":"feeGrowthInside0LastX128","type":"uint256"},{"internalType":"uint256","name":"feeGrowthInside1LastX128","type":"uint256"},{"internalType":"uint128","name":"tokensOwed0","type":"uint128"},{"internalType":"uint128","name":"tokensOwed1","type":"uint128"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"protocolFees","outputs":[{"internalType":"uint128","name":"token0","type":"uint128"},{"internalType":"uint128","name":"token1","type":"uint128"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint8","name":"feeProtocol0","type":"uint8"},{"internalType":"uint8","name":"feeProtocol1","type":"uint8"}],"name":"setFeeProtocol","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"slot0","outputs":[{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"internalType":"int24","name":"tick","type":"int24"},{"internalType":"uint16","name":"observationIndex","type":"uint16"},{"internalType":"uint16","name":"observationCardinality","type":"uint16"},{"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"},{"internalType":"uint8","name":"feeProtocol","type":"uint8"},{"internalType":"bool","name":"unlocked","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"int24","name":"tickLower","type":"int24"},{"internalType":"int24","name":"tickUpper","type":"int24"}],"name":"snapshotCumulativesInside","outputs":[{"internalType":"int56","name":"tickCumulativeInside","type":"int56"},{"internalType":"uint160","name":"secondsPerLiquidityInsideX128","type":"uint160"},{"internalType":"uint32","name":"secondsInside","type":"uint32"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"recipient","type":"address"},{"internalType":"bool","name":"zeroForOne","type":"bool"},{"internalType":"int256","name":"amountSpecified","type":"int256"},{"internalType":"uint160","name":"sqrtPriceLimitX96","type":"uint160"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"swap","outputs":[{"internalType":"int256","name":"amount0","type":"int256"},{"internalType":"int256","name":"amount1","type":"int256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"int16","name":"","type":"int16"}],"name":"tickBitmap","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"tickSpacing","outputs":[{"internalType":"int24","name":"","type":"int24"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"int24","name":"","type":"int24"}],"name":"ticks","outputs":[{"internalType":"uint128","name":"liquidityGross","type":"uint128"},{"internalType":"int128","name":"liquidityNet","type":"int128"},{"internalType":"uint256","name":"feeGrowthOutside0X128","type":"uint256"},{"internalType":"uint256","name":"feeGrowthOutside1X128","type":"uint256"},{"internalType":"int56","name":"tickCumulativeOutside","type":"int56"},{"internalType":"uint160","name":"secondsPerLiquidityOutsideX128","type":"uint160"},{"internalType":"uint32","name":"secondsOutside","type":"uint32"},{"internalType":"bool","name":"initialized","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"token0","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"token1","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]
'''

coinurl = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
coinparam = {
    'symbol' : 'ETH',
    'convert' : 'USD',
}

w3 = Web3(HTTPProvider("https://restless-delicate-lake.discover.quiknode.pro/1372d20d14a4f985176e424e61ad6df1e403f8a3/"))

#ERC-20 tokens use floating point math. Reserve counts are stored as 
addrbook = {
    "eth" : "0x0000000000000000000000000000000000000000",
    "usdc" : "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "bat" : "0x0D8775F648430679A709E98d2b0Cb6250d2887EF",
    "dai" : "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "weth" : "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "usdt" : "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "uni" : "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
    "paxg" : "0x45804880De22913dAFE09f4980848ECE6EcbAf78",
    "wbtc" : "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    "badger" : "0x3472A5A71965499acd81997a54BBA8D852C6E53d",
}

coindecimals = {
    "eth" : 18,
    "usdc" : 6,
    "bat" : 18,
    "dai" : 18,
    "weth" : 18,
    "usdt" : 6,
    "uni" : 18,
    "paxg" : 18,
    "wbtc" : 8,
    "badger" : 18,

}

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
    threading.Timer(5.0, queryGraph, (query,)).start()
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

gas_prices = estimateGasTest()
meangas = statistics.mean(gas_prices)
mediangas = statistics.median(gas_prices)
print(meangas/10**9)
print(mediangas/10**18)

max_wait_seconds = 120
print(getLatestBlockRewardFee(75))
#print(w3.eth.estimate_gas({'to': '0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8', 'from':w3.eth.coinbase, 'value': 12345}))
uniswap_wrapper = Uniswap(metamaskaddress, privatekey, infuraurl, version = 3)
web3_f = w3.eth.contract(address=uniswap_wrapper.address, abi=factoryABI)
estimated_gas = web3_f.functions.withdraw(w3.toWei(0.1, "ether")).estimateGas()
print(estimated_gas)

#data = getPool('eth', 'usdc', "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8")
#raw_pair = float(data['data']['pool']['volumeToken0'])/ float(data['data']['pool']['volumeToken1'])
#sqrprice = float(data['data']['pool']['sqrtPrice'])
#print(sqrtToPrice(sqrprice, coindecimals['eth'] - coindecimals['usdc']))
#def get_pair(token0, token1):

#print(calcPoolExchange(5734, 6379363, 5734*6379363, 1))
#print(triCalcAbsolute(1.5028, 1/0.8678, 1/1.3021))
#print(triCalcPercent(1.5028, 1/0.8678, 1/1.3021))

#print(getLastTransaction('0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8'))