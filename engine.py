from binance.client import Client
from binance.enums import *
import time
import HFT_algo

ddd = [0,1,2,3,4,5,6,7,8,9]

#Exchanges
sym = 'BNBETH'
input_str = input('Enter your Exchange, default BNBETH:')
if input_str != '':
    sym = input_str

amount = 10
input_str = input('Enter your amount, default 10:')
if input_str != '':
    amount = int(input_str)

#Sampling CONFIG
samplingRate = 0.5
samples_per_min = 30

input_str = input('Enter your sampling rate, default 0.5:')
if input_str != '':
    samplingRate = float(input_str)

input_str = input('Enter your average window, default 30:')
if input_str != '':
    samples_per_min = int(input_str)

MAX_HIST = 40 * samples_per_min

fee = 0.0005
limit = False


#Enable Trading
TradingEnabled = False
FastFill = True


#load api key 
f = open("API.txt", "r")
lines = f.read().splitlines()
api_key = lines[0].split(" ")[2]
secret = lines[1].split(" ")[2]

#Open client
client = Client(api_key,secret)

def time_now():
    t = time.localtime()
    s = '[' + str(t.tm_year) + '/' +str(t.tm_mon)+ '/'+str(t.tm_mday)+ ' '+ str(t.tm_hour) + ':' +str(t.tm_min)+ ':'+str(t.tm_sec) + ']'
    return s

def Perform(action,price,quan):
    if action == 0:
        return
    if action == 1:
        side = Client.SIDE_SELL
        actionStr = "SELL"
    elif action == 2:
        side = Client.SIDE_BUY
        actionStr = "BUY"

    if TradingEnabled == False:
        print(actionStr + "@" + price)
        return

    else:
        order = client.create_order(
                symbol=sym,
                side=side,
                type = 'MARKET',
                quantity=quan)
        #print("Made an order:" + actionStr + "@" + str(order['price']) +" x" + str(quan))
        #print (order)
        return order

def get_per_min_history(history):
    i = 0;
    per_min_hist = []
    while i < len(history):
        if i%samples_per_min == 0:
            per_min_hist.append(0)
        per_min_hist[int(i/samples_per_min)]+= float(history[i])/samples_per_min;
        i+=1;
    return per_min_hist;
    

history = []
orders = client.get_my_trades(symbol=sym,limit = 1)
cost = orders[0]['price']
lastAction = 1
lastBuyTs = time.clock()
lastSellTs = lastBuyTs

print (time_now() + "HFT BOT Starting now for " + sym)
print ("Amount = " + str(amount) +" SamplingRate = " + str(samplingRate) + " Sample Avg window: "+ str(samples_per_min))

if (FastFill):
    print("FastFill Enabled... starting filling with faster sampling rate")

    originalSR = samplingRate
    #use 5sec sample as a min
    samplingRate = 0.075

while(1):
    run = False
    
    #GET DATA
    #1. price
    trades = client.get_recent_trades(symbol=sym,limit = 1)
    price = trades[0]['price']
    #print(time_now()+price+"   TS:"+str(trades[0]['time']))

    #2 order depth
    asks = []
    bids = []
    if 0:
        depth = client.get_order_book(symbol=sym)
        asks = depth['asks']
        bids = depth['bids']
    
    #3. history for MACD, RSI
    history.append(price)
    if len(history) > MAX_HIST:
        history = history[1:MAX_HIST+1]
        per_min_history = get_per_min_history(history);
        run = True
    elif len(history)%(int(MAX_HIST/20)) == 0:
        print (time_now() + str(int(len(history)/(int(MAX_HIST/20)))*5) + "% history filled")

    if FastFill == True and len(history) == MAX_HIST:
        samplingRate = originalSR
        FastFill = False
        print("FastFill Completed, now samping rate = " + str(samplingRate))
        print("-----------------------------------------------------------")

    if(run):
        #Call HFT module to decide
        currTs = time.clock()
        action = HFT_algo.HFT(cost, lastBuyTs, currTs, price, fee, per_min_history, asks, bids, lastAction)

        #Perform action
        if (action > 0 and action != lastAction):
            order = Perform(action,price,amount)
            lastAction = action
        
            if action == 2:
                if TradingEnabled:
                    if order != None:
                        if order['status']  != 'FILLED':
                            sleep(0.1)
                    orders = client.get_my_trades(symbol=sym,limit = 1)
                    cost = orders[0]['price']
                else:
                    cost = price
                print("Bought@" + str(cost) +" x" + str(amount))
                lastBuyTs = time.clock()
            elif action ==1:
                if TradingEnabled:
                    if order != None:
                        if order['status']  != 'FILLED':
                            sleep(0.1)
                    orders = client.get_my_trades(symbol=sym,limit = 1)
                    sell_price = orders[0]['price']
                else:
                    sell_price = price

                if(sell_price < 0.999 * price):
                    print("Trading Lantency cause > 0.1% lost! Sell Price: "+ str(sell_price)+ " Last Price: " + str(price))

                profit = (float(sell_price)-float(cost))/float(cost) - fee
                
                print("Last Sell Price: " + str(sell_price) + " Cost: " + str(cost) + " Profit%: " + str(profit*100) + " Time Taken: "+ str(currTs-lastSellTs) + " s")
                lastSellTs = currTs                

    time.sleep(samplingRate)

    

