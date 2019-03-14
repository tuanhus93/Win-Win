import sys
import shift
import time
import numpy
import datetime

signal_number = 2
cut_off = 0.06


# Data Processing
def point(trader, stock):
    bp = trader.getBestPrice(stock)
    bid = bp.getBidPrice()
    ask = bp.getAskPrice()
    average = (bid+ask)/2
    return average


# High at index 0, low at index 1, open at 2, close at 3
def bar(data):
    data_bar = []
    high = max(data)
    data_bar.append(high)
    low = min(data)
    data_bar.append(low)
    open_bar = data[0]
    data_bar.append(open_bar)
    close_bar = data[-1]
    data_bar.append(close_bar)
    return data_bar


def conversion(high, low):
    max_bar = max(high[-9:])
    min_bar = min(low[-9:])
    con = (max_bar + min_bar) / 2
    return con


def base(high, low):
    max_bar = max(high[-26:])
    min_bar = min(low[-26:])
    base_line = (max_bar + min_bar) / 2
    return base_line


def leadingA(con_line, base_line):
    return (con_line[-26] + base_line[-26]) / 2


def leadingB(high, low):
    max_bar = max(high[:52])
    min_bar = min(low[:52])
    return (max_bar + min_bar) / 2


# Trading Decision
# Ichimoku signal
def Ichimoku(con_line, base_line, A, B):
    if con_line > base_line > A > B:
        return 1
    elif con_line < base_line < A < B:
        return -1
    else:
        return 0


# RSI signal
def calculate_rsi(data):
    no_bar = 5
    up = 0
    down = 0
    for i in range(-6, -1):
        change = data[i+1] - data[i]
        if change >= 0:
            up += change/no_bar
        else:
            down += abs(change)/no_bar
    if down == 0:
        relative_strength_index = 100
    else:
        relative_strength = up/down
        relative_strength_index = 100 - 100/(1+relative_strength)
    return relative_strength_index


def get_m(data):
    if data[-3] < 30 and data[-2] > 30 and data[-1] > 30 and data[0] > 30:
        m_signal = 1
    elif data[-3] > 70 and data[-2] < 70 and data[-1] < 70 and data[0] < 70:
        m_signal = -1
    else:
        m_signal = 0
    return m_signal


def execution(trader, symbol, signal):
    item = trader.getPortfolioItem(symbol)
    share = item.getShares()
    position = abs(share*item.getPrice())
    left = 50000 - position
    if signal == "OFFSET":
        if share > 0:
            trader.submitOrder(shift.Order(shift.Order.MARKET_SELL, symbol, abs(share)))
        else:
            trader.submitOrder(shift.Order(shift.Order.MARKET_BUY, symbol, abs(share)))
    elif signal == "SELL":
        best = trader.getOrderBook(symbol, shift.OrderBookType.GLOBAL_BID, 1)[0]
        size = int(left / (100 * best.price))
        trader.submitOrder(shift.Order(shift.Order.MARKET_SELL, symbol, size))
    else:
        best = trader.getOrderBook(symbol, shift.OrderBookType.GLOBAL_ASK, 1)[0]
        size = int(left / (100 * best.price))
        trader.submitOrder(shift.Order(shift.Order.MARKET_BUY, symbol, size))


# Signal come from the signal_list table
def controller(trader, signal_list, symbol, count):
    if signal_list[symbol][0] == 1:
        # if Ichimoku has buy signal
        # then either buy with confirming or neutral RSI signal
        if signal_list[symbol][1] == 0 or signal_list[symbol][1] == 1:
            execution(trader, symbol, "BUY")
            count += 1
            return count
        # or offset the current position
        else:
            execution(trader, symbol, "OFFSET")
            count += 1
            return count
    elif signal_list[symbol][0] == -1:
        # the other way around
        if signal_list[symbol][1] == 0 or signal_list[symbol][1] == -1:
            execution(trader, symbol, "SELL")
            count += 1
            return count
        else:
            execution(trader, symbol, "OFFSET")
            count += 1
            return count
    else:
        return count


# pass closings as dictionary and symbols as complete stock_list
def standard_deviation(closings, symbols):
    variance = 0
    for s in symbols:
        variance += numpy.var(closings[s][-30:])/len(symbols)
    st = numpy.sqrt(variance)
    print(st)
    if st <= 0.16:
        return "LOW"
    elif 0.16 < st <= 1:
        return "HIGH"
    else:
        return "CRASH"


# Termination Process
def kill_everything(trader, count):
    try:
        for item in trader.getPortfolioItems().values():
            trial = 0
            while item.getShares != 0:
                if item.getShares() > 0:
                    sell = shift.Order(shift.Order.MARKET_SELL, item.getSymbol(), int(item.getShares() / 100))
                    trader.submitOrder(sell)
                    count += 1
                elif item.getShares() < 0:
                    buy = shift.Order(shift.Order.MARKET_BUY, item.getSymbol(), -int(item.getShares() / 100))
                    trader.submitOrder(buy)
                    count += 1
                trial += 1

                if item.getShares != 0 & trial < 10:
                    time.sleep(0.5)
                if item.getShares != 0 & trial >= 10:
                    break

    except Exception as e:
        print(e)
    return count


def fulfill_trades(trader, stock_list, count):
    try:
        while count < 10:
            buy = shift.Order(shift.Order.MARKET_BUY, stock_list[0], 1)
            trader.submitOrder(buy)
            sell = shift.Order(shift.Order.MARKET_SELL, stock_list[0], 1)
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
def check_single_pl(trader, stock_list, table, volatility, count):
    try:
        if volatility == "High":
            threshold = 0.05
        elif volatility == "Low":
            threshold = 0.02
        else:
            threshold = 0

        for s in stock_list:
            if table[s][0] < threshold * table[s][1] * table[s][2]:
                count = kill_it(trader, s, count)
            elif table[s][0] < cut_off * table[s][1] * table[s][2]:
                count = kill_it(trader, s, count)

    except Exception as e:
        print(e)

    return count


# check total loss
def check_total_pl(trader, stock_list, table, volatility, count):
    try:
        if volatility == "High":
            threshold = 0.025
        elif volatility == "Low":
            threshold = 0.0025
        else:
            threshold = 0

        unrealized_pl = 0
        for s in stock_list:
            unrealized_pl += table[s][0]

        if unrealized_pl < -1000000 * threshold:
            kill_everything(trader, count)
            fulfill_trades(trader, count, stock_list)
            return True

    except Exception as e:
        print(e)

    return False


# Portfolio Print
def portfolio(trader, blocklist):
    print("Portfolio after hour: %s" % datetime.datetime.now())
    print("Buying Power\tTotal Shares\tTotal P&L\tTimestamp")
    print("%12.2f\t%12d\t%9.2f\t%26s" % (trader.getPortfolioSummary().getTotalBP(),
                                         trader.getPortfolioSummary().getTotalShares(),
                                         trader.getPortfolioSummary().getTotalRealizedPL(),
                                         trader.getPortfolioSummary().getTimestamp()))
    print("The following equities are on the blocklist:")
    print(*blocklist)
    print()

    print("Symbol\t\tShares\t\tPrice\t\tP&L\t\tTimestamp")
    for item in trader.getPortfolioItems().values():
        print("%6s\t\t%6d\t%9.2f\t%7.2f\t\t%26s" %
              (item.getSymbol(), item.getShares(), item.getPrice(), item.getRealizedPL(), item.getTimestamp()))

    return


# Trade Print
def trade_print(data, trader, symbol, close):
    item = trader.getPortfolioItem(symbol)
    new_share = item.getShares()-data[symbol][1]
    if new_share == 0:
        return data
    new_price = (item.getShares()*item.getPrice()-data[symbol][1]*data[symbol][2])/new_share
    if new_share != 0:
        print("%s has %d for %f" % (symbol, new_share, new_price))
    data[symbol][0] = close[-1] - data[symbol][1] * data[symbol]*[2]
    data[symbol][1] = item.getShares()
    data[symbol][2] = item.getPrice()
    return data


def main(argv):
    trader = shift.Trader("winwin")
    try:
        trader.connect("initiator.cfg", "E46Cgsvn3g3dunmc")
        trader.subAllOrderBook()
    except shift.IncorrectPassword as e:
        print(e)
    except shift.ConnectionTimeout as e:
        print(e)

    stock_list = ["MMM", "AXP", "AAPL", "BA", "CAT", "CVX", "CSCO", "KO", "DIS", "DWDP", "XOM","GS","HD","IBM","INTC","JNJ","JPM","MCD", "MRK", "MSFT", "NKE", "PFE", "PG", "TRV", "UTX", "UNH", "VZ", "V","WMT","WBA"]
    signal_list={}
    trade_list = {}
    high_bars = {}
    low_bars = {}
    close_bars = {}
    con_line = {}
    base_line = {}
    leadA = {}
    leadB = {}
    timer = 0
    start = 110*60  # put number of minutes * 60
    end = 380*60  # put number of minutes *60
    data_point = {}
    count = 0
    blocklist = {}
    rsi_dict = {}
    m_signal = {}
    volatility = ""

    # I, M, unr_P&L, share, average_ori_price
    for s in stock_list:
        signal_list[s] = numpy.zeros(signal_number)
        trade_list[s] = [0, 0, 0]
        m_signal[s] = 0
    print("START at %s" % datetime.datetime.now())
    while True:
        while True:
            # adding timer to check
            timer += 10
            time.sleep(9.9)
            # getting data point each 10 sec
            for s in stock_list:
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
                    else:
                        high_bars[s].append(temp_bar[0])
                        low_bars[s].append(temp_bar[1])
                        close_bars[s].append(temp_bar[3])
                    # clear out the memory
                    data_point[s].clear()

            # stop gathering data to do data analysis
            if stock_list[-1] in low_bars.keys():
                # 78 is for 52 bar plotted 26 bar forward
                if len(low_bars[stock_list[-1]]) == 78:
                    break

        # Volatility
        if timer == start:
            volatility = standard_deviation(close_bars, stock_list)

        # Print
        if timer % 1800 == 0:
            time.sleep(0.001)
            portfolio(trader, blocklist)
            print(trade_list)

        # DATA ANALYSIS
        for s in stock_list:
            if s not in con_line.keys():
                con_line[s] = [conversion(high_bars[s], low_bars[s])]
                base_line[s] = [base(high_bars[s], low_bars[s])]
                rsi_dict[s] = [calculate_rsi(close_bars[s])]
                leadB[s] = [leadingB(high_bars[s], low_bars[s])]
            else:
                con_line[s].append(conversion(high_bars[s], low_bars[s]))
                base_line[s].append(base(high_bars[s], low_bars[s]))
                rsi_dict[s].append(calculate_rsi(close_bars[s]))
                leadB[s].append(leadingB(high_bars[s], low_bars[s]))

            if len(con_line[s]) > 26:
                if s not in leadA.keys():
                    leadA[s] = [leadingA(con_line[s], base_line[s])]
                else:
                    leadA[s].append(leadingA(con_line[s], base_line[s]))
            # only trade after 2 hours
            if timer >= start:
                if volatility == "HIGH":
                    signal_list[s][1] = get_m(rsi_dict[s])
                signal_list[s][0] = Ichimoku(con_line[s], base_line[s], leadA[s], leadB[s])
                count = controller(trader, signal_list, s, count)
                trade_list[s] = trade_print(trade_list, trader, s, close_bars)
            # Memory Optimization
            if len(con_line[s]) == 32:
                con_line[s].pop(0)
                base_line[s].pop(0)
                leadA[s].pop(0)
                leadB[s].pop(0)
                rsi_dict[s].pop(0)

            # remove oldest data point for optimization
            high_bars[s].pop(0)
            low_bars[s].pop(0)
            close_bars[s].pop(0)

        if timer >= start:
            # checking single item in portfolio
            count = check_single_pl(trader, stock_list, trade_list, volatility, count)

            # termination check for pl
            if check_total_pl(trader, stock_list, trade_list, volatility, count):
                print("Killed by check_total_pl")
                break

        # termination check for time and trade count
        if timer == end:
            count = kill_everything(trader, count)
            print("Killed by kill_everything")
            if count < 10:
                fulfill_trades(trader, count, stock_list)
                break
            break

    portfolio(trader, blocklist)
    print(trade_list)

    trader.disconnect()

    return


if __name__ == "__main__":
    main(sys.argv)