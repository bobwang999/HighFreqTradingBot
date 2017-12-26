import numpy as np

data = [46.125,47.125,46.4375,46.9375,44.9375,44.2500,44.6250,45.7500,47.8125,47.5625,47.0000,44.5625,46.3125,47.6875,46.6875,45.6875,43.0625,43.5625,44.8750,43.6875, 46.125,47.125,46.4375,46.9375,44.9375,44.2500,44.6250,45.7500,47.8125,47.5625,47.0000,44.5625,46.3125,47.6875,46.6875,45.6875,43.0625,43.5625,44.8750,43.6875,46.125,47.125,46.4375,46.9375,44.9375,44.2500,44.6250,45.7500,47.8125,47.5625,47.0000,44.5625,46.3125,47.6875,46.6875,45.6875,43.0625,43.5625,44.8750,43.6875,46.125,47.125,46.4375,46.9375,44.9375,44.2500,44.6250,45.7500,47.8125,47.5625,47.0000,44.5625,46.3125,47.6875,46.6875,45.6875,43.0625,43.5625,44.8750,43.6875,46.125,47.125,46.4375,46.9375,44.9375,44.2500,44.6250,45.7500,47.8125,47.5625,47.0000,44.5625,46.3125,47.6875,46.6875,45.6875,43.0625,43.5625,44.8750,43.6875]
macd_data = [459.99,448.85,446.06,450.81,442.8,448.97,444.57,441.4,430.47,420.05,431.14,425.66,430.58,431.72,437.87,428.43,428.35,432.5,443.66,455.72,454.49,452.08,452.73,461.91,463.58,461.14,452.08,442.66,428.91,429.79,431.99,427.72,423.2,426.21,426.98,435.69,434.33,429.8,419.85,426.24,402.8,392.05,390.53,398.67,406.13,405.46,408.38,417.2,430.12,442.78,439.29,445.52,449.98,460.71,458.66,463.84,456.77,452.97,454.74,443.86,428.85,434.58,433.26,442.93,439.66,441.35]

def EMA1(values, window):
    #print(values)
    #print(window)
    
    weights = np.exp(np.linspace(-1,0,window))
    weights /= weights.sum()
    return np.convolve(values, weights)[window-1:len(values)]

def EMA(values, window):
    firstSMA = sum(values[:window])/window
    last_ema = firstSMA
    ema = [last_ema]    
    i = window
    while i < len(values):
        last_ema = values[i]*(2/(window+1))+last_ema*(1-(2/(window+1)))
        ema.append(last_ema)
        i+=1
    return ema

def MACD(values):
    if(len(values) < 34):
        return [0,0]
    short_term = EMA(values, 12)
    #print(short_term)
    long_term = EMA(values, 26)
    #print(long_term)
    short_term = short_term[14:]
    macd = [a - b for a, b in zip(short_term, long_term)] 
    #print (macd)
    signal = EMA(macd, 9)
    diff = [a - b for a, b in zip(macd[8:], signal)]

    #print(diff)

    #POSITIVE, BUY
    if(diff[len(diff)-1] > 0 and diff[len(diff)-2] >= 0 and diff[len(diff)-1] > diff[len(diff)-2]):
        i = 3
        while len(diff)-i >= 0 and i < 5:
            if diff[len(diff)-i] < 0:
                #print("MACD buy :")
                #print(diff[len(diff)-min(5,len(diff)):])
                return [2, diff[len(diff)-1]]
            i+=1;

    #NEGAT
    if(diff[len(diff)-1] < 0 and diff[len(diff)-2] <= 0 and diff[len(diff)-1] < diff[len(diff)-2]):
        i = 3
        while len(diff)-i >= 0 and i < 5:
            if diff[len(diff)-i] > 0:
                #print("MACD sell :")
                #print(diff[len(diff)-min(5,len(diff)):])
                return [1,diff[len(diff)-1]]
            i+=1;
    return [0,diff[len(diff)-1]];


def RSI(values, window = 14):
    if(len(values)<window):
        return 50.0
    
    gain = []
    loss = []

    RS = 0
    RSI = 0
    
    i = 1
    while i< window + 1:
        if values[i] >= values[i-1]:
            gain.append(values[i]-values[i-1])
            loss.append(0)
        else:
            gain.append(0)
            loss.append(values[i-1]-values[i])
        i+=1
    #print(gain)
    #print(loss)
    #now i == window, calculate first RS
    avg_loss = sum(loss)/window
    avg_gain = sum(gain)/window
    if avg_loss != 0:
        RS = avg_gain/avg_loss
    RSI = 100 - 100/(1+RS)
    
    while i < len(values):
        if values[i] >= values[i-1]:
            gain = values[i]-values[i-1]
            loss = 0
        else:
            gain = 0
            loss = values[i-1]-values[i]
        avg_gain = (avg_gain*(window-1)+gain)/window
        avg_loss = (avg_loss*(window-1)+loss)/window
        if avg_loss != 0:
            RS = avg_gain/avg_loss
            RSI = 100 - 100/(1+RS)
        #print (RS)
        #print(RSI)
        i+=1
    if avg_loss == 0:
        if avg_gain == 0:
            RSI = 50
        else:
            RSI = 100
    
    return RSI
    

def HFT(cost, lastBuyTs, currTs, price, fee, history, asks, bids, lastAction):
    #print("LEN: "+str(len(history)))
    #print(history)

    MACDvalue = MACD(history);
    RSIvalue = RSI(history);

    #print("RSI: " + str(RSIvalue))
    #print("MACD: "+str(MACDvalue))

    if(lastAction != 1):
        # 1. Stop loss
        if float(price) < 0.9 * float(cost):
            if (max(history[:-2])< 0.9 * float(cost)):
                print("cost: " + str(cost))
                print("price: " + str(price))
                return 1;
            #any time 5%
        if(float(price) > float(cost) * 1.05):
            
            print("cost: " + str(cost))
            print("price: " + str(price))
            
            return 1;

        #10mins 3%
        if(float(price) > float(cost) * 1.03 and currTs-lastBuyTs > 600):
            print("cost: " + str(cost))
            print("price: " + str(price))
            return 1;

        #30mins 2%
        if(float(price) > float(cost) * 1.02 and currTs-lastBuyTs > 1800):
            print("cost: " + str(cost))
            print("price: " + str(price))
            return 1;

        #RSI pull back + MACD dropping or negative
        if(RSIvalue > 70 and MACDvalue[1] < 0):
            print("RSI: " + str(RSIvalue))
            print("MACD: "+str(MACDvalue))
            return 1;

        if(MACDvalue[0] == 1 and RSIvalue > 60):
            print("RSI: " + str(RSIvalue))
            print("MACD: "+str(MACDvalue))
            return 1;

    if(lastAction != 2):
        #decide buy first
        if(RSIvalue < 30):
            print("RSI: " + str(RSIvalue))
            print("MACD: "+str(MACDvalue))
            return 2;
        if(RSIvalue < 65 and MACDvalue[0] == 2):
            print("RSI: " + str(RSIvalue))
            print("MACD: "+str(MACDvalue))
            return 2;

    return 0


if __name__ == '__main__':
    i = 34
    while i < len(macd_data):
        MACD(macd_data[:i])
        i+=1
    if 0:
        print(HFT(100, 100, 5000,20, 0.0005, data, 0, 0))
        print(HFT(100, 100, 5000,120, 0.0005, data, 0, 0))
        print(HFT(100, 100, 500,105.1, 0.0005, data, 0, 0))
        print(HFT(100, 100, 500,105, 0.0005, data, 0, 0))
        print(HFT(100, 100, 500,104, 0.0005, data, 0, 0))
        print(HFT(100, 100, 900,104, 0.0005, data, 0, 0))
        print(HFT(100, 100, 5000,101, 0.0005, data, 0, 0))
