my_username = "winwin"
my_password = "E46Cgsvn3g3dunmc"


            if(timer%1200==0):
                t= timer/3600
                print("%12.2f hours passed" % t)
                print("Buying Power\tTotal Shares\tTotal P&L\tTimestamp")
                print("%12.2f\t%12d\t%9.2f\t%26s" % (trader.getPortfolioSummary().getTotalBP(),
                                                     trader.getPortfolioSummary().getTotalShares(),
                                                     trader.getPortfolioSummary().getTotalRealizedPL(),
                                                     trader.getPortfolioSummary().getTimestamp()))
                print("Symbol\t\tShares\t\tPrice\t\tP&L\t\tTimestamp")
                for item in trader.getPortfolioItems().values():
                    print("%6s\t\t%6d\t%9.2f\t%7.2f\t\t%26s" %
                          (item.getSymbol(), item.getShares(), item.getPrice(), item.getRealizedPL(),
                           item.getTimestamp()))
