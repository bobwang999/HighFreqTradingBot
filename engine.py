from binance.client import Client
from binance.enums import *
import time

#load api key 
f = open("API.txt", "r")
lines = f.read().splitlines()
api_key = lines[0].split(" ")[2]
secret = lines[1].split(" ")[2]

#Open client
client = Client(api_key,secret)


def trial():
    candles = client.get_klines(symbol='BNBBTC', interval=KLINE_INTERVAL_1MINUTE)
    print("Candle")
    count = 0
    for c in candles:
        count+=1
    print (candles[0])
    print(count)

    depth = client.get_order_book(symbol='BNBBTC')
    print("depth")
    #print(depth)

    tickers = client.get_ticker()
    print("tickers")
    print(tickers[0])

    trades = client.get_recent_trades(symbol='BNBBTC')
    print('Trades')
    print(trades[0]['price'])
    

trial()

    

