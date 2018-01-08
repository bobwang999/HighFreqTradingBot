from binance.client import Client
from binance.enums import *
import time
import HFT_algo

#Enable Trading
TradingEnabled = True
FastFill = False
useRSI = False
printOut = True

#Exchanges
sym = 'BNBETH'
input_str = input('Enter your Exchange, default BNBETH:')
if input_str != '':
    sym = input_str

amount = 10
input_str = input('Enter your amount, default 10:')
if input_str != '':
    if input_str == '0':
        TradingEnabled = False
    amount = int(input_str)

#Sampling CONFIG
samplingRate = 1
samples_per_min = 60

input_str = input('Enter your sampling rate, default 1:')
if input_str != '':
    samplingRate = float(input_str)

input_str = input('Enter your average window, default 60:')
if input_str != '':
    samples_per_min = int(input_str)

MAX_HIST = 40 * samples_per_min

input_str = input('Enable Fast Fill (Y/N), default no?:')
if input_str == 'Y':
    FastFill = True

input_str = input('Enable RSI (Y/N), default no?:')
if input_str == 'Y':
    useRSI = True

input_str = input('Slience Mode (Y/N), default no?:')
if input_str == 'Y':
    printOut = False


fee = 0.0005
limit = False



#load api key 
f = open("API.txt", "r")
lines = f.read().splitlines()
api_key = lines[0].split(" ")[2]
secret = lines[1].split(" ")[2]
f.close()

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
        LOG(actionStr + "@" + price)
        return

    else:
        order = client.create_order(
                symbol=sym,
                side=side,
                type = 'MARKET',
                quantity=quan)
        #LOG("Made an order:" + actionStr + "@" + str(order['price']) +" x" + str(quan))
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

def LOG(s):
    if(printOut):
        print(s)
    with open ("LOG_"+str(StartTime)+".txt","a") as file:
        file.write(s+'\n')

def checkSwitch():
    r = False
    with open("switch.txt","r") as switch:
        if (switch.readline() =="1"):
            r = True
    return r
    

accProfit  = 0
initialBuy = 0
initialBuyTs = 0
history = []
orders = client.get_my_trades(symbol=sym,limit = 1)
cost = orders[0]['price']
lastAction = 1

StartTime = time.clock()
lastBuyTs = StartTime
lastSellTs = lastBuyTs
currTs = StartTime
profit_if_no_sell = 0

LOG(time_now() + "HFT BOT Starting now for " + sym)
LOG("Amount = " + str(amount) +" SamplingRate = " + str(samplingRate) + " Sample Avg window: "+ str(samples_per_min))
LOG("TRADING:" + str(TradingEnabled))

if (FastFill):
    LOG("FastFill Enabled... starting filling with faster sampling rate")

    originalSR = samplingRate
    #use 5sec sample as a min
    samplingRate = 0.075

try:
    while(1):
        if(checkSwitch() == False):
            LOG("Exiting as it is turned off...")
            break
        run = False
        
        #GET DATA
        #1. price
        trades = client.get_recent_trades(symbol=sym,limit = 1)
        price = trades[0]['price']
        #LOG(time_now()+price+"   TS:"+str(trades[0]['time']))

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
            LOG("FastFill Completed, now samping rate = " + str(samplingRate))
            LOG("-----------------------------------------------------------")

        if(run):
            #Call HFT module to decide
            currTs = time.clock()
            action = HFT_algo.HFT(cost, lastBuyTs, currTs, price, fee, per_min_history, asks, bids, lastAction, useRSI)

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

                    #add fees to price
                    cost = str((1+fee) * float(cost))
                    LOG("Bought@" + str(cost) +" x" + str(amount))
                    lastBuyTs = time.clock()
                    if (initialBuy == 0):
                        initialBuy = cost
                        initialBuyTs = currTs
                elif action ==1:
                    if TradingEnabled:
                        if order != None:
                            if order['status']  != 'FILLED':
                                sleep(0.1)
                        orders = client.get_my_trades(symbol=sym,limit = 1)
                        sell_price = orders[0]['price']
                    else:
                        sell_price = price

                    if(float(sell_price) < 0.999 * float(price)):
                        LOG("Trading Lantency cause > 0.1% lost! Sell Price: "+ str(sell_price)+ " Last Price: " + str(price))

                    profit = (float(sell_price) * (1-fee)-float(cost))/float(cost)
                    LOG("Last Sell Price: " + str(sell_price) + " Cost: " + str(cost) + " Profit%: " + str(profit*100) + " Time Taken: "+ str(currTs-lastSellTs) + " s")

                    accProfit += profit
                    profit_if_no_sell = (float(sell_price) * (1-fee) -float(initialBuy))/float(initialBuy)
                    LOG("Accumulated Profit: " + str(accProfit*100) + " Profit if no sell: " + str(profit_if_no_sell*100) + " Time Taken: "+ str(currTs-initialBuyTs) + " s")
                    lastSellTs = currTs                

        time.sleep(samplingRate)
finally:
    LOG("ENDING... Accumulated Profit: " + str(accProfit*100) + " Profit if no sell: " + str(profit_if_no_sell*100) + " Time Taken: "+ str(currTs-initialBuyTs) + " s")
    

