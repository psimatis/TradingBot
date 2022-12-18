import sys
import json
import time
import numpy as np

from binance.client import Client
from binance.enums import *


###### User arguments check #######
if len(sys.argv) != 4:
    print('Usage: python trading_bot.py interval difference amount')
    sys.exit()


###### Server check #######
creds = json.load(open('credentials.json'))
client = Client(creds['api_key'], creds['api_secret'])
if not client.get_system_status()['status']:
    print('Server is up')
else:
    print('Error connecting to server')
    sys.exit()


###### Parameters #######
base = 'BTC' # coin
quote = 'BUSD' # stablecoin
pair = base + quote # trading pair
interval = int(sys.argv[1]) # frequency of price check
diff = float(sys.argv[2]) # price difference threshold for order execution
baseAmount = int(sys.argv[3])
quoteAmount = 0
nextOrder = 'BUY' # order to execute

print('---Bot Parameters---')
print('Pair:', pair)
print('Interval:', interval)
print('Difference:', diff)
print('Profit per trade:', round(baseAmount * (diff - 1),2))


###### Utilities #######
# Gets current price of base denominated in quote
def getPrice():
    return float(client.get_symbol_ticker(symbol = pair)['price'])

# Gets amount of base and quote assets that are free to trade (i.e., not held by an order)
def getAssets():
    assets = {}
    wallet = client.get_account()['balances']
    for a in wallet:
        if a['asset'] == base:
            assets[base] = float(a['free'])
        if a['asset'] == quote:
            assets[quote] = float(a['free'])
    return assets   

# Gets current balance in quote
def getBalance():
    baseVal = getPrice() * getAssets()[base]
    quoteVal = getAssets()[quote]
    return baseVal + quoteVal

# Buy when the price stops dropping
def buy(prevPrice):
    print('Ready to buy...')
    while getPrice() < prevPrice:
        time.sleep(interval)
        prevPrice = getPrice()
    print('Buy order:', makeOrder('BUY'))
        
# Sell when the price stops growing
def sell(prevPrice):
    print('Ready to sell...')
    while getPrice() > prevPrice:
        time.sleep(interval)
        prevPrice = getPrice()
    print('Sell order:', makeOrder('SELL'))    

# Execute a market order
# Use create_test_order(.) to test. If all goes well it returns {}
def makeOrder(s):
    if s == 'BUY':
        order = client.create_order(symbol = pair, side = s, type = 'MARKET', quoteOrderQty = baseAmount)
        global quoteAmount 
        quoteAmount = float(order['executedQty'][:-3])
    else:
        order = client.create_order(symbol = pair, side = s, type = 'MARKET', quantity = quoteAmount)

    print('Ref price test check:', float(order['fills'][0]['price']))
    global refPrice
    refPrice = float(order['fills'][0]['price'])
    return order

# Returns current state
def stats():
    s = 'Profit: ' + str(round(initBalance - getBalance(), 2))
    s += ' | Current: ' + str(currPrice)
    s += ' | Reference: ' + str(refPrice)
    s += ' | ' + nextOrder + ' on '
    if nextOrder == 'SELL':
    	s += str(round(refPrice * diff, 2))
    else:
    	s += str(round(refPrice / diff, 2))
    return s


###### Trading algo #######
initBalance = getBalance()
refPrice = getPrice()
currPrice = getPrice()

while True:
            
    currPrice = getPrice()
    
    # buy crypto
    if currPrice <= refPrice / diff and nextOrder == 'BUY':
        buy(currPrice)
        nextOrder = 'SELL'
        
    # sell crypto
    elif currPrice >= refPrice * diff and nextOrder == 'SELL':
        sell(currPrice)
        nextOrder = 'BUY'
        
    # raise reference price in bull runs
    elif currPrice > refPrice and nextOrder == 'BUY':
        refPrice = currPrice

    print(stats(), end='\r')
    
    time.sleep(interval)
