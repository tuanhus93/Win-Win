import shift
import time
from multiprocessing import Process


def avgbar():
    print('executing avgbar')
    time.sleep(2)
    bits = {}
    asks = {}
    dp = {}
    for s in stocklist:
        dp[s] = 0
        bits[s] = []
        asks[s] = []
    count = 0
    while True:
        count += 1
        for s in stocklist:
            pbit = trader.getBestPrice(s).getBidPrice()
            pask = trader.getBestPrice(s).getAskPrice()
            dp[s] = dp[s] + pbit + pask
            if count % 6 == 0:
                avg = dp[s] / 12
                avgbars[s].append(avg)
                dp[s] = 0
                count = 0
                # print(avgbars)
        time.sleep(10)


def lagging():
    for s in stocklist:
        price = trader.getLastPrice(s)
        tlagging[s].append(price)
    time.sleep(60)


def conversion():
    time.sleep(3120)
    while True:
        for s in stocklist:
            max_bar = max(avgbars[s][-1:-10])
            min_bar = min(avgbars[s][-1:-10])
            con = (max_bar + min_bar) / 2
            tcon[s].append(con)
        time.sleep(60)


def base():
    time.sleep(3120)
    while True:
        for s in stocklist:
            max_bar = max(avgbars[s][-1:-27])
            min_bar = min(avgbars[s][-1:-27])
            ba = (max_bar + min_bar) / 2
            tbase[s].append(ba)
        time.sleep(60)


def leadingA():
    time.sleep(3121)
    t = -1  # t is the current bar
    while True:
        t += 1
        for s in stocklist:
            tleadingA[s].append((tbase[s][t] + tcon[s][t])/2)
        time.sleep(60)


def leadingB():
    time.sleep(3120)
    time.sleep(3120)
    while True:
        for s in stocklist:
            max_bar = max(avgbars[s][-1:-53])
            min_bar = min(avgbars[s][-1:-53])
            ba = (max_bar + min_bar) / 2
            tbase[s].append(ba)
        time.sleep(60)


def output():
    time.sleep(3122)
    t = -1
    while True:
        t += 1
        for s in stocklist:
            toutput[s] = [tcon[t], tbase[t], tleadingA[t], tleadingB[t]]
        print(toutput)


"""

def release():
    time.sleep(3650)
    while True:
        tlagging.pop(0)
        avgbars.pop(0)
        tcon.pop(0)
        tbase.pop(0)
        tleadingA.pop(0)
        tleadingA.pop(0)
        time.sleep(60)
        
"""

trader = shift.Trader("democlient")
try:
    trader.connect("initiator.cfg", "password")
    trader.subAllOrderBook()
except shift.IncorrectPassword as e:
    print(e)
except shift.ConnectionTimeout as e:
    print(e)

time.sleep(2)

stocklist = ['BA', 'GS', 'MMM', 'UNH', 'HD', 'AAPL', 'MCD', 'CAT', 'IBM', 'TRV']
tlagging = {}
avgbars = {}
tcon = {}
tbase = {}
tleadingA = {}
tleadingB = {}
toutput = {}


for stock in stocklist:
    avgbars[stock] = []
    tlagging[stock] = []
    tcon[stock] = []
    tbase[stock] = []
    tleadingA[stock] = []
    tleadingB[stock] = []
    toutput[stock] = []

pa = Process(target=avgbar, name='a', args=())
pl = Process(target=lagging, name='c', args=())
pc = Process(target=conversion, name='c', args=())  # conversion
pb = Process(target=base, name='b', args=())  # base
pla = Process(target=leadingA, name='la', args=())  # leadingA
plb = Process(target=leadingB, name='lb', args=())  # leadingB
pout = Process(target=output, name='op', args=())  # produce the final table, 5*10
# rel = Process(target=release, name='rel', args=())  # only if necessary, release the memory

