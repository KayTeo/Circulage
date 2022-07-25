from random import sample
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
