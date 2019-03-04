import shift
import sys
import time
import csv

def demo07(trader):
    """
    This method provides information on the structure of PortfolioSummary and PortfolioItem objects:
     getPortfolioSummary() returns a PortfolioSummary object with the following data:
     1. Total Buying Power (totalBP)
     2. Total Shares (totalShares)
     3. Total Realized Profit/Loss (totalRealizedPL)
     4. Timestamp of Last Update (timestamp)

     getPortfolioItems() returns a dictionary with "symbol" as keys and PortfolioItem as values, with each providing the following information:
     1. Symbol (getSymbol())
     2. Shares (getShares())
     3. Price (getPrice())
     4. Realized Profit/Loss (getRealizedPL())
     5. Timestamp of Last Update (getTimestamp())
    :param trader:
    :return:
    """

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


def strongsignal(con_line, base, A, B, symbol, trader, count):
    print("START")
    if con_line > base > A > B:
        order = trader.getOrderBook(symbol, shift.OrderBookType.GLOBAL_ASK,1)[0]
        size = min(int(1000/order.price), order.size)
        trader.submitOrder(shift.Order(shift.Order.MARKET_BUY,symbol,size))
        count += 1
        print("BUY")
    elif con_line < base < A < B:
        order = trader.getOrderBook(symbol, shift.OrderBookType.GLOBAL_ASK, 1)[0]
        size = min(int(1000 / order.price), order.size)
        trader.submitOrder(shift.Order(shift.Order.MARKET_SELL, symbol, size))
        count += 1
        print("SELL")
    return count

def weak_1(con_line ,base,symbol ,trader, count):
    print("START")
    if con_line[0] < con_line[1] and base[1] <= base[0] and con_line[0] < base[0]:
        if con_line[2] > base[2] and con_line[3] > base[3]:
            trader.submitOrder(shift.Order(shift.Order.MARKET_BUY, symbol, 1))
            count+=1
            print("BUY")
    elif con_line[0] > con_line[1] and base[1] >= base[0] and con_line[0] > base[0]:
        if con_line[2] < base[2] and con_line[3] < base[3]:
            trader.submitOrder(shift.Order(shift.Order.MARKET_SELL, symbol, 1))
            count += 1
            print("SELL")
    return count

# Pass the last 5 close lead A lead B
def weak_2(close, A, B, symbol, trader, count):
    print("START")
    if close[0] < close[1] and close[1] >= max(A[1], B[1]) and close[0] < max(A[0], B[0]) and max(close) == close[5]:
        if close[2] >= max(A[2], B[2]) and close[3] >= max(A[3], B[3]) and close[4] >= max(A[4], B[4]) and close[5] >= max(A[5], B[5]):
            trader.submitOrder(shift.Order(shift.Order.MARKET_BUY, symbol, 1))
            count += 1
            print("BUY")
    elif close[0] > close[1] and close[1] <= min(A[1], B[1]) and close[0] > min(A[0], B[0]) and min(close) == close[5]:
        if close[2] <= min(A[2], B[2]) and close[3] <= min(A[3], B[3]) and close[4] <= min(A[4], B[4]) and close[5] <= min(A[5], B[5]):
            trader.submitOrder(shift.Order(shift.Order.MARKET_SELL, symbol, 1))
            count += 1
            print("SELL")
    return count

#close is the vector of the last 52 close
# size of con_line & base = 4
# size of A, B = 6
def controller(close, con_line, base, A, B, symbol, trader, count):
    strongsignal(con_line[len(con_line)-1], base[len(base)-1], A[len(A)-1], B[len(A)-1], symbol, trader, count)
    if max(close)>max(A[len(A)-1], B[len(A)-1]):
        return count
    elif min(close)<min(A[len(A)-1], B[len(A)-1]):
        return count
    weak_1(con_line ,base,symbol ,trader, count)
    weak_2(close, A, B, symbol, trader, count)
    return count

def main(argv):
    trader=shift.Trader("democlient")
    try:
        trader.connect("initiator.cfg", "password")
        trader.subAllOrderBook()
    except shift.IncorrectPassword as e:
        print(e)
    except shift.ConnectionTimeout as e:
        print(e)
    time.sleep(1)

    # count=1
    # controller(close,con_line,base,A,B,symbol,trader,count)
    # time.sleep(2)
    # demo07(trader)
    trader.disconnect()

    return


if __name__ == "__main__":
    main(sys.argv)


