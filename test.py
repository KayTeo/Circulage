from requests import Request, Session, TooManyRedirects
from web3 import Web3, EthereumTesterProvider
import functions
import pandas as pd
import plotly.express as px
import time

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport



eth = "0x0000000000000000000000000000000000000000"
bat = "0x0D8775F648430679A709E98d2b0Cb6250d2887EF"
dai = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
usdc = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"



def connectUni():
    uniswap_wrapper = Uniswap(metamaskaddress, privatekey, infuraurl, version = 3)

    session = Session()
    session.headers.update(coinheaders)

    try:
        response = session.get(coinurl, params = coinparam).json()
        data = response['data']
        ethdata = data['ETH']
        pricedata = ethdata['quote']
        usdprice = pricedata['USD']
        ethprice = usdprice['price']

    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)
 


#print(pricedata)
#This library always assumes the routing token1 -> (w)eth -> token2 for token -> token transactions (on Uniswap v2) and gets the prices directly
# from the contract (we're not computing prices ourselves here, just asking the contract for the price given a route).
#Different tokens have different decimals, e.g. 6 for USDC and 18 for WETH, leading one token of USDC being worth much more than one unit of WETH in raw data
#Uniswap pairs are ordered so the currency with the lowest address comes

def getInputPrice(token0, token1):
    raw_price = uniswap_wrapper.get_price_input(addrbook[token0], addrbook[token1], 10 ** addrdecimals[token0])
    #adjusted_price = raw_price / (10**(addrbook[token0 + "-decimal"] - addrbook[token1 + "-decimal"]))
    adjusted_price = raw_price / 10** int(addrdecimals[token1])
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

#while True:
#print('eth/usdc/udst'+ str(getInputPrice("eth", "dai")))

#test1 = functions.triCalcPercent(getInputPrice("eth", "usdc"), getInputPrice("eth", "usdt"), getInputPrice("usdc", "usdt"))
#test1 = getInputPrice("usdc", "usdt")
#print(test1)
#print(w3.eth.get_balance("0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc"))

sample_transport = RequestsHTTPTransport(
    url = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2',
    #
    verify=True,
    retries=3,
)

client = Client(
    transport = sample_transport
)

query = '''
query {
    pairs (first: 10, where: {volumeUSD_gt: "10000000"})
    {
    volumeUSD
    token0 {
        symbol
    }
    token1 {
        symbol
        }
    }
}
'''

eth_usdc_query = '''
{
  pool(id: "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8") {
    tick
    token0 {
      symbol
      id
      decimals
    }
    token1 {
      symbol
      id
      decimals
    }
    feeTier
    sqrtPrice
    liquidity
  }
}
'''




#queryGraph(query)



start = time.time()

for i in range(1):
    print(response)

end = time.time()
print(end - start)


#print(response)
sqrtprice = int(response['data']['pool']['sqrtPrice'])
print(functions.sqrtToPrice(sqrtprice))

print(functions.sqrtToPrice(sqrtprice, functions.coindecimals['eth'] - functions.coindecimals['usdc']))
#TO DO
#1. def function for pulling raw pair data
#2. def function for calculating raw transaction fee
#3. def function for calculating probable charge of gas fees + auctioning
#4. Get swap data?

#sqrtPriceX96 = sqrt(price) * 2 ** 96
