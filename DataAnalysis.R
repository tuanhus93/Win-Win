
#Set WD and load libraries
library(plotly)

#preliminaries
barobs <- 6 #number of observations per bar
lag1 <- 26 #number of points for lagging line
bas <- 26 #number of points for base line 
lb <- 52 #number of points for leading indicator b
conv <- 9 #number of points for conversion line

Observations <- read.csv("Feb26Data.csv", header = TRUE, sep= ",")

#prepare lines for all 30 stocks
Analysis <- matrix(NA,ncol=9,nrow=nrow(Observations))
Analysis <- array(NA,c(30,nrow(Analysis)/barobs,9))
dimnames(Analysis)[[3]] <- c("Max","Min","Close","Open","Lagging","Conversion","Base","LeadA","LeadB")

for (j in 1:30){
  for(i in 1:nrow(Analysis[j,,])){
    Analysis[j,i,"Max"] <- max(Observations[((i-1)*barobs+1):(i*barobs),j+1]) #find max, min, open, and close for point
    Analysis[j,i,"Min"] <- min(Observations[((i-1)*barobs+1):(i*barobs),j+1])
    Analysis[j,i,"Open"] <- Observations[((i-1)*barobs+1),j+1]
    Analysis[j,i,"Close"] <- Observations[(i*barobs),j+1]

    if(i>conv){ #create conversion line
      Analysis[j,i,"Conversion"] <- (max(Analysis[j,(i-conv):(i-1),"Max"])+min(Analysis[j,(i-conv):(i-1),"Min"]))/2
    }
    if(i>bas){ #create base line
      Analysis[j,i,"Base"] <- (max(Analysis[j,(i-bas):(i-1),"Max"])+min(Analysis[j,(i-bas):(i-1),"Min"]))/2
    }
    #create Lead A (not to be used in trading competition)
    Analysis[j,i,"LeadA"] <- (Analysis[j,i,"Conversion"]+Analysis[j,i,"Base"])/2
    
    if(i>lb){ #create Lead B line
      Analysis[j,i,"LeadB"] <- (max(Analysis[j,(i-lb):(i-1),"Max"])+min(Analysis[j,(i-bas):(i-1),"Min"]))/2
    }
  }
}

for (j in 1:30){ #create Laffinf line
  for(i in 1:nrow(Analysis[j,,])){
    if(i < nrow(Analysis[j,,])-lag1){
      Analysis[j,i,"Lagging"] <- Analysis[j,i+lag1,"Close"]}
  }
}

j <- 2 #change j from 1-30 to access plot for different stock; adjust axes if necessary
plot_ly(x = ~seq(1,nrow(Analysis[j,,]),1), type="candlestick",
        open = ~Analysis[j,,"Open"], close = ~Analysis[j,,"Close"],
        high = ~Analysis[j,,"Max"], low = ~Analysis[j,,"Min"],name = colnames(Observations)[j+1]) %>%
add_lines(x = ~seq(1,nrow(Analysis[j,,]),1), y = ~Analysis[j,,"Base"], line = list(color = 'black', width = 1.5), inherit = F,name = "Base") %>% 
add_lines(x = ~seq(1,nrow(Analysis[j,,]),1), y = ~Analysis[j,,"Lagging"], line = list(color = 'blue', width = 1.5), inherit = F,name = "Lagging") %>%  
add_lines(x = ~seq(1,nrow(Analysis[j,,]),1), y = ~Analysis[j,,"Conversion"], line = list(color = 'yellow', width = 1.5), inherit = F,name = "COnversion") %>%  
#add_lines(x = ~seq(1,nrow(Analysis[j,,]),1), y = ~Analysis[j,,"LeadA"], line = list(color = 'blue', width = 1.5), inherit = F,name = "LeadA")  %>%
add_lines(x = ~seq(1,nrow(Analysis[j,,]),1), y = ~Analysis[j,,"LeadB"], line = list(color = 'magenta', width = 1.5), inherit = F,name = "LeadB")  

#Save data if necessary
write.csv(Analysis[8,,],"TestData")

Analysis[8,,]

