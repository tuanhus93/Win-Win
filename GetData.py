import getopt
import math
import numpy
import shift
import sys
import time
import array
import goodcbfs
import pandas


#Get last price every 10 seconds
def data_Aquisition():

    #universe of all Dow Jones securities
    Dow30 = ["MMM","AXP","AAPL","BA","CAT","CVX","CSCO", "KO", "DIS", "DWDP",
             "XOM","GS","HD","IBM","INTC","JNJ","JPM","MCD","MRK","MSFT","NKE",
             "PFE","PG","TRV","UTX","UNH","VZ", "V","WMT","WBA"]

    #Set up trader
    client_id_number = 2 # client ID number (test001 - test010)
    simulation_duration = 390 # duration of simulation (in minutes); 390 minutes for one complete trading day
    simulation_seconds = simulation_duration*60 # number of seconds in simulation
    client_id = f"test{str(client_id_number).zfill(3)}"
    trader = shift.Trader(client_id)
    trader.connect("initiator.cfg", "password") #connect to SHIFT
    trader.subAllOrderBook() #to get bid and ask prices

    #list to fill with security prices
    allprices = []

    i = 0
    while i <= simulation_seconds:

        # list to fill with security prices for current iteration
        currentprices =[]

        #wait one second if i == 0
        if i == 0:
            time.sleep(1)
        if i % 3600 == 0: #print for every hour
            print(i/3600)

        currentprices.append(i) #add time to currentprices
        for j in range(0,len(Dow30)): #add all prices to currentprices
              currentprices.append((trader.getBestPrice(Dow30[j]).getBidPrice()+trader.getBestPrice(Dow30[j]).getAskPrice())/2)

        allprices.append(currentprices) #add currentprices/ iteration to allprices

        #wait 60 seconds and increment i before next iteration
        time.sleep(60)
        i += 60


    cols = ["Second","MMM","AXP","AAPL","BA","CAT","CVX","CSCO", "KO", "DIS", "DWDP",
             "XOM","GS","HD","IBM","INTC","JNJ","JPM","MCD","MRK","MSFT","NKE",
             "PFE","PG","TRV","UTX","UNH","VZ", "V","WMT","WBA"]

    #Send prices to csv file
    output = pandas.DataFrame(data = allprices,columns=cols)
    output.to_csv('Jan0318', sep='\t')

    #disconnect trader
    trader.disconnect()
    return 0

data_Aquisition()