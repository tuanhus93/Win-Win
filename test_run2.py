import sys
import shift
import time
import datetime


##Data Processing
def point(trader, stock):
    bp = trader.getBestPrice(stock)
    bid = bp.getBidPrice()
    ask = bp.getAskPrice()
    average = (bid + ask) / 2
    return average


# High at index 0, low at index 1, open at 2, close at 3
def bar(data):
    data_bar = []
    high = max(data)
    data_bar.append(high)
    low = min(data)
    data_bar.append(low)
    open = data[0]
    data_bar.append(open)
    close = data[-1]
    data_bar.append(close)
    return data_bar


def conversion(high, low):
    max_bar = max(high[-9:])
    min_bar = min(low[-9:])
    con = (max_bar + min_bar) / 2
    return con


def base(high, low):
    max_bar = max(high[-26:])
    min_bar = min(low[-26:])
    base = (max_bar + min_bar) / 2
    return base


def leadingA(conversion, base):
    if len(conversion) < 26:
        return
    return (conversion[-26] + base[-26]) / 2


def leadingB(high, low):
    if len(high) < 52:
        return
    max_bar = max(high[:52])
    min_bar = min(low[:52])
    return (max_bar + min_bar) / 2


## Trading Decision
def strongsignal(con_line, base, A, B, symbol, trader, count,timer):
    if con_line > base > A > B:
        order = trader.getOrderBook(symbol, shift.OrderBookType.GLOBAL_ASK, 1)[0]
        size = min(int(1000 / order.price), order.size)
        trader.submitOrder(shift.Order(shift.Order.MARKET_BUY, symbol, size))
        count += 1
        print("BUY %f lots of %s w/ Strong at minute %f for %f " % (size, symbol,timer/60, trader.getBestPrice(symbol).getAskPrice()))
    elif con_line < base < A < B:
        order = trader.getOrderBook(symbol, shift.OrderBookType.GLOBAL_ASK, 1)[0]
        size = min(int(1000 / order.price), order.size)
        trader.submitOrder(shift.Order(shift.Order.MARKET_SELL, symbol, size))
        count += 1
        print("SOLD %f lots of %s w/ Strong at minute %f for %f" % (size, symbol,timer/60, trader.getBestPrice(symbol).getBidPrice()))
    return count


def weak_1(con_line, base, symbol, trader, count,timer):
    if con_line[0] < con_line[1] and base[1] <= base[0] and con_line[0] < base[0]:
        if con_line[2] > base[2] and con_line[3] > base[3]:
            trader.submitOrder(shift.Order(shift.Order.MARKET_BUY, symbol, 1))
            count += 1
            print("BUY 1 Lot of %f w/ Weak_1 at minute %s at %f " % (symbol, timer/60,trader.getBestPrice(symbol).getAskPrice()))
    elif con_line[0] > con_line[1] and base[1] >= base[0] and con_line[0] > base[0]:
        if con_line[2] < base[2] and con_line[3] < base[3]:
            trader.submitOrder(shift.Order(shift.Order.MARKET_SELL, symbol, 1))
            count += 1
            print("SELL 1 Lot of %f w/ Weak_1 at minute %s at %f" % (symbol,timer/60, trader.getBestPrice(symbol).getBidPrice()))
    return count


# Pass the last 5 close lead A lead B
def weak_2(close, A, B, symbol, trader, count,timer):
    if close[0] < close[1] and close[1] >= max(A[1], B[1]) and close[0] < max(A[0], B[0]) and max(close) == close[5]:
        if close[2] >= max(A[2], B[2]) and close[3] >= max(A[3], B[3]) and close[4] >= max(A[4], B[4]) and close[
            5] >= max(A[5], B[5]):
            trader.submitOrder(shift.Order(shift.Order.MARKET_BUY, symbol, 1))
            count += 1
            print("BUY 1 Lot of %f w/ Weak_2 at minute %s at %f " % (symbol, timer/60,trader.getBestPrice(symbol).getAskPrice()))
    elif close[0] > close[1] and close[1] <= min(A[1], B[1]) and close[0] > min(A[0], B[0]) and min(close) == close[5]:
        if close[2] <= min(A[2], B[2]) and close[3] <= min(A[3], B[3]) and close[4] <= min(A[4], B[4]) and close[
            5] <= min(A[5], B[5]):
            trader.submitOrder(shift.Order(shift.Order.MARKET_SELL, symbol, 1))
            count += 1
            print("SELL 1 Lot of %f w/ Weak_2 at minute %s at %f" % (symbol,timer/60, trader.getBestPrice(symbol).getBidPrice()))
    return count


# close is the vector of the last 52 close
# size of con_line & base = 4
# size of A, B = 6
def controller(close, con_line, base, A, B, symbol, trader, count,timer):
    strongsignal(con_line[-1], base[-1], A[-1], B[-1], symbol, trader, count,timer)
    if max(close) > max(A[-1], B[-1]):
        return count
    elif min(close) < min(A[-1], B[-1]):
        return count
    weak_1(con_line[-1:-4], base[-1:-4], symbol, trader, count,timer)
    weak_2(close[-1:-6], A[-1:-6], B[-1:-6], symbol, trader, count,timer)
    return count


##Termination Process

def kill_everything(trader, count):
    try:
        for item in trader.getPortfolioItems().values():
            if item.getShares() > 0:
                sell = shift.Order(shift.Order.MARKET_SELL, item.getSymbol(), int(item.getShares() / 100))
                trader.submitOrder(sell)
                count += 1
            elif item.getShares() < 0:
                buy = shift.Order(shift.Order.MARKET_BUY, item.getSymbol(), -int(item.getShares() / 100))
                trader.submitOrder(buy)
                count += 1
    except Exception as e:
        print(e)
    return count


def fulfill_trades(trader, count, stocklist):
    try:
        while count < 10:
            buy = shift.Order(shift.Order.MARKET_BUY, stocklist[0], 1)
            trader.submitOrder(buy)
            sell = shift.Order(shift.Order.MARKET_SELL, stocklist[0], 1)
            trader.submitOrder(sell)
            count += 2

    except Exception as e:
        print(e)

    return count


# remove huge loss position
def kill_it(trader, item, count):
    try:
        if item.getShares() > 0:
            sell = shift.Order(shift.Order.MARKET_SELL, item.getSymbol(), int(item.getShares() / 100))
            trader.submitOrder(sell)
            count += 1
        elif item.getShares() < 0:
            buy = shift.Order(shift.Order.MARKET_BUY, item.getSymbol(), -int(item.getShares() / 100))
            trader.submitOrder(buy)
            count += 1

    except Exception as e:
        print(e)
    return count


# use kill_it to check the portfolio
def check_single_pl(trader, blocklist, count):
    try:
        for item in trader.getPortfolioItems().values():
            if item.getRealizedPL() < -20000:
                count = kill_it(trader, item, count)
                blocklist[item.getSymbol()] = 1
    except Exception as e:
        print(e)

    return count


# check total loss
def check_total_pl(trader, count, stocklist):
    try:
        if trader.getPortfolioSummary().getTotalRealizedPL() < -100000:
            kill_everything(trader, count)
            fulfill_trades(trader, count, stocklist)
            return True

    except Exception as e:
        print(e)

    return False


# Portfolio Print
def portfolio(trader):
    print("Buying Power\tTotal Shares\tTotal P&L\tTimestamp")
    print("%12.2f\t%12d\t%9.2f\t%26s" % (trader.getPortfolioSummary().getTotalBP(),
                                         trader.getPortfolioSummary().getTotalShares(),
                                         trader.getPortfolioSummary().getTotalRealizedPL(),
                                         trader.getPortfolioSummary().getTimestamp()))

    print()

    print("Symbol\t\tShares\t\tPrice\t\tP&L\t\tTimestamp")
    for item in trader.getPortfolioItems().values():
        print("%6s\t\t%6d\t%9.2f\t%7.2f\t\t%26s" %
              (item.getSymbol(), item.getShares(), item.getPrice(), item.getRealizedPL(), item.getTimestamp()))

    return


def main(argv):
    trader = shift.Trader("winwin")
    try:
        trader.connect("initiator.cfg", "E46Cgsvn3g3dunmc")
        trader.subAllOrderBook()
    except shift.IncorrectPassword as e:
        print(e)
    except shift.ConnectionTimeout as e:
        print(e)
    time.sleep(1)

    stocklist = ["MMM", "AXP", "AAPL", "BA", "CAT", "CVX", "CSCO", "KO", "DIS", "DWDP", "XOM", "GS", "HD", "IBM",
                 "INTC", "JNJ", "JPM", "MCD", "MRK", "MSFT", "NKE", "PFE", "PG", "TRV", "UTX", "UNH", "VZ", "V", "WMT",
                 "WBA"]
    # stocklist = ['BA']
    high_bars = {}
    low_bars = {}
    close_bars = {}
    con_line = {}
    base_line = {}
    leadA = {}
    leadB = {}
    timer = 0
    start = 7200
    end = 22800
    data_point = {}
    count = 0
    blocklist = {}

    while True:
        while True:

            # getting data point each 10 sec
            for s in stocklist:
                now = datetime.datetime.now()
                if s not in data_point.keys():
                    data_point[s] = [point(trader, s)]
                else:
                    data_point[s].append(point(trader, s))

                # making a data bar from 6 data points
                if len(data_point[s]) == 6:
                    temp_bar = bar(data_point[s])
                    if s not in high_bars.keys():
                        high_bars[s] = [temp_bar[0]]
                        low_bars[s] = [temp_bar[1]]
                        close_bars[s] = [temp_bar[3]]
                        #print("bar: %s " % now)
                    else:
                        high_bars[s].append(temp_bar[0])
                        low_bars[s].append(temp_bar[1])
                        close_bars[s].append(temp_bar[3])
                        #print(timer)
                        #print("bar: %s " % now)

                    # clear out the memory
                    data_point[s].clear()

            # adding timer to check
            timer += 10
            time.sleep(9.9)


            # stop gathering data to do data analysis
            if stocklist[-1] in low_bars.keys():
                if len(low_bars[stocklist[-1]]) == 78:
                    break

        # DATA ANALYSIS
        for s in stocklist:
            now = datetime.datetime.now()
            if s not in leadA.keys():
                con_line[s] = [conversion(high_bars[s], low_bars[s])]
                base_line[s] = [base(high_bars[s], low_bars[s])]
                leadA[s] = [leadingA(con_line[s], base_line[s])]
                leadB[s] = [leadingB(high_bars[s], low_bars[s])]
                #print("data: %s " % now)
            else:
                con_line[s].append(conversion(high_bars[s], low_bars[s]))
                base_line[s].append(base(high_bars[s], low_bars[s]))
                leadA[s].append(leadingA(con_line[s], base_line[s]))
                leadB[s].append(leadingB(high_bars[s], low_bars[s]))
                #print("data: %s " % now)

            # Trading execution
            if len(con_line[s]) == 32:
                #print("Optimize bar: %s " % now)
                con_line[s].pop(0)
                base_line[s].pop(0)
                leadA[s].pop(0)
                leadB[s].pop(0)
                # only trade after 2 hours
                if timer >= start:
                    count = controller(close_bars[s], con_line[s], base_line[s], leadA[s], leadB[s], s, trader, count,timer)

            # remove oldest data point for optimization
            high_bars[s].pop(0)
            low_bars[s].pop(0)
            close_bars[s].pop(0)

        # checking single item in portfolio
        count = check_single_pl(trader, blocklist, count)

        # termination check for pl
        if check_total_pl(trader, count, stocklist):
            print("Killed by check_total_pl")
            break

        # termination check for time and trade count
        if timer == end:
            count = kill_everything(trader, count)
            print("Killed by kill_everything")
            if count < 10:
                fulfill_trades(trader, count, stocklist)
                break
            break

        # Portfolio print
        if timer % 1800 == 0:
            print("Portfolio after %s hours: " % (timer / 3600))
            portfolio(trader)


    trader.disconnect()

    return


if __name__ == "__main__":
    main(sys.argv)