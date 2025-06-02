import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
from apiKeys import *
def marketmaker(startingstrike,chain1):
    MMM=0
    for i, row in chain1.iterrows():
      if (startingstrike-chain1["Strike"][i])>0:
          MMM=MMM+(startingstrike-chain1["Strike"][i])*chain1["Open Interest"][i]
    return MMM
def marketmakerT(startingstrike,chain1,chain2):
    MMM=0
    if(len(chain1)>len(chain2)):
        for i, row in chain1.iterrows():
            if (startingstrike-chain1["Strike"][i])>0:
                MMM=MMM+(startingstrike-chain1["Strike"][i])*chain1["Open Interest"][i]
        return MMM
    else:
        for i, row in chain2.iterrows():
          if (chain2["Strike"][i]-startingstrike)>0:
              MMM=MMM+(chain2["Strike"][i]-startingstrike)*chain2["Open Interest"][i]
    return MMM         
def marketmakerP(startingstrike,chain2):
    MMM=0
    for i, row in chain2.iterrows():
      if (chain2["Strike"][i]-startingstrike)>0:
          MMM=MMM+(chain2["Strike"][i]-startingstrike)*chain2["Open Interest"][i]
    return MMM
def screnner(ticker,bardisplay,expirationIndex):
    symbol = ticker  # Change this to the symbol you want
    #get price
    responseC = requests.get('https://api.tradier.com/v1/markets/quotes',
        params={'symbols': symbol, 'greeks': 'false'},
        headers={'Authorization': tradier, 'Accept': 'application/json'}
    )
    price=responseC.json()['quotes']['quote']['last']
    #get expirations
    responseB = requests.get('https://api.tradier.com/v1/markets/options/expirations',
        params={'symbol': symbol, 'includeAllRoots': 'true', 'strikes': 'true'},
        headers={'Authorization': tradier, 'Accept': 'application/json'}
        )
    expirations= responseB.json()
    expirationList=[]
    for i in range(len(expirations['expirations']['expiration'])):
        expirationList.append(expirations['expirations']['expiration'][i]["date"])


    expiration = expirationList[expirationIndex]  # Change this to the expiration date you want
    #get chains
    response = requests.get('https://api.tradier.com/v1/markets/options/chains',
        params={'symbol': symbol, 'expiration': expiration, 'greeks': 'true'},
        headers={'Authorization': tradier, 'Accept': 'application/json'}
    )

    # Process API response
    if response.status_code == 200:
        data = response.json()
        betachain = data['options']['option']
        # Do something with the options chain data
    else:
        print(f'Error: {response.status_code} - {response.text}')
    callBeta=[]
    putBeta=[]
    for i in range( len(betachain)):
        makeup=betachain[i]["option_type"]
        if betachain[i]["option_type"]=='call':
            callBeta.append(betachain[i])
        makeup=betachain[i]["option_type"]
        if betachain[i]["option_type"]=='put':
            putBeta.append(betachain[i])

    # for i in callBeta:
    contractNamesC=[]
    StrikePricesC=[]
    VolumeC=[]
    OIC=[]
    IVC=[]
    contractNamesP=[]
    StrikePricesP=[]
    VolumeP=[]
    OIP=[]
    IVP=[] 
    for i in range(len(callBeta)):
        contractNamesC.append(callBeta[i]["symbol"])
        StrikePricesC.append(callBeta[i]["strike"])
        VolumeC.append(callBeta[i]["volume"])
        OIC.append(callBeta[i]["open_interest"])
        try:
            IVC.append(callBeta[i]["greeks"]["mid_iv"])
        except (KeyError, TypeError) as e:
        # handle the exception here
            IVC.append(0)
    for i in range(len(putBeta)):
        contractNamesP.append(putBeta[i]["symbol"])
        StrikePricesP.append(putBeta[i]["strike"])
        VolumeP.append(putBeta[i]["volume"])
        OIP.append(putBeta[i]["open_interest"])
        try:
            IVP.append(putBeta[i]["greeks"]["mid_iv"])
        except (KeyError, TypeError) as e:
            # handle the exception here
            IVP.append(0)   
    dataC = {'Contract Name': contractNamesC,
            'Strike': StrikePricesC,
            'Volume': VolumeC,
            'Implied Volatility': IVC,
            'Open Interest': OIC
            }
    dataP = {'Contract Name': contractNamesP,
            'Strike': StrikePricesP,
            'Volume': VolumeP,
            'Implied Volatility': IVP,
            'Open Interest': OIP
            }      
    adf = pd.DataFrame(dataC, columns=['Contract Name','Strike', 'Volume','Implied Volatility',
                                       'Open Interest'
           ])
    bdf=pd.DataFrame(dataP, columns=['Contract Name','Strike', 'Volume','Implied Volatility'
                                     ,'Open Interest'])
    chainNew={"calls":adf,"puts":bdf}
    ##############################################################################################
    #MMTA is just the MMt devided by average MMT near strike price

    expirations=expirationList
    ticker=symbol
    a=adf 

    # Print the put options'
    b=bdf

    current_price = price
    price=current_price
    if current_price > 50:
        current_price = round(current_price * 2) / 2
    else:
        current_price = round(current_price * 4) / 4
        
    ###### section to get closest strike
    ##chain = options.get_options_chain(ticker, expirations[expirationdate])
    chain = chainNew
    # Get the list of strike prices
    chain3=chain
    strikes = chain["calls"]["Strike"].tolist()
    strikesP=chain["puts"]["Strike"].tolist()
    ###################
    # Find the strike closest to the current stock price
    closest_strike = min(strikes, key=lambda x: abs(x - current_price))
    closest_strikeP = min(strikesP, key=lambda x: abs(x - current_price))
    # Find the index of the closest strike
    index_strike = strikes.index(closest_strike)
    index_strikeP = strikesP.index(closest_strikeP)
    chain["calls"]=chain["calls"][:][index_strike-9:index_strike+9]
    chain["puts"]=chain["puts"][:][index_strikeP-9:index_strikeP+9]
    strikes = chain["calls"]["Strike"].tolist()
    strikesP=chain["puts"]["Strike"].tolist()
    ##########

    testing=chain["calls"]
    testingP=chain["puts"]
    df = pd.DataFrame(testing)
    for i, row in df.iterrows():
        if df["Open Interest"][i]=="-":
            df["Open Interest"][i]=0
    df['Open Interest'] = pd.to_numeric(df['Open Interest'], errors='coerce')
    MM=[]
    MMT=[]
    MMTA=[]
    for i, row in df.iterrows():
        MM.append(marketmaker(df["Strike"][i],df))
        MMT.append(0)
        MMTA.append(0)
    df["MM"]=MM
    df["MMT"]=MMT
    df["MMTA"]=MMT
    MMP=[]
    dfp = pd.DataFrame(testingP)
    for i, row in dfp.iterrows():
        if dfp["Open Interest"][i]=="-":
            dfp["Open Interest"][i]=0
    dfp['Open Interest'] = pd.to_numeric(dfp['Open Interest'], errors='coerce')
    MMT=[]
    MMTA=[]
    for i, row in dfp.iterrows():
        MMP.append(marketmakerP(dfp["Strike"][i],dfp))
        MMT.append(0)
        MMTA.append(0)
    dfp["MM"]=MMP
    dfp["MMT"]=MMT
    dfp["MMTA"]=MMT
    # =============================================================================
    # dfp["MMtotal"]=df["MM"]-dfp["MM"]
    # df["MMtotal"]=df["MM"]-dfp["MM"]
    # =============================================================================
    # Set the minimum open interest threshold to include options
    max_oi = float(chain["calls"]["Open Interest"].max())
    min_oi = max_oi * 0.075
    # Find the strike closest to the current stock price

    closest_strike = min(strikes, key=lambda x: abs(x - current_price))
    closest_strikeP = min(strikesP, key=lambda x: abs(x - current_price))
    # Find the index of the closest strike
    index_strike = strikes.index(closest_strike)
    index_strikeP = strikesP.index(closest_strikeP)
    # Slice the options to only include 10 strikes above and below the closest strike
    num_strikes = 6 
    # =============================================================================
    # call_options = np.array(chain["calls"][index_strike-num_strikes:index_strike+num_strikes+1][df['Open Interest'] >= min_oi][df['Open Interest'] >= 300])
    # put_options = np.array(chain["puts"][index_strike-num_strikes:index_strike+num_strikes+1][dfp["Open Interest"] >= min_oi][dfp["Open Interest"] >= 300])
    # =============================================================================
    call_options = np.array(df[index_strike-num_strikes:index_strike+num_strikes+1])
    put_options = np.array(dfp[index_strikeP-num_strikes:index_strikeP+num_strikes+1])
    # transofrom these into only strike and oi 
    call_options=call_options[:,[1,4,5,6,7]]
    put_options=put_options[:,[1,4,5,6,7]]
    # section to get total market maker
    maxMMT=0
    maxMMT_Index=0
    for i in range(len(call_options)):
        for j in range(len(put_options)):
            strike = call_options[i][0]
            if strike == put_options[j][0]:
                call_oi = call_options[i][2]
                put_oi = put_options[j][2]
                call_options[i][3] =  abs( call_oi - put_oi)*100/1000000
                put_options[j][3]=  abs( call_oi - put_oi)*100/1000000
                if call_options[i][3]>maxMMT:
                    maxMMT=call_options[i][3]
                    maxMMT_Index=[i]
                if put_options[j][3]>maxMMT:
                    maxMMT=put_options[j][3]

    average = sum(call_options[:,3]) / len(call_options[:,3])
    if average==0:
        average=1
    min_MM = min(call_options[:,3])
    #print(min_MM,"im here min MM")
    #print(min(call_options[:,3]),"im here min(call_options[:,3]) ")
    #print(call_options[:,3],"im here ")
    min_indices = [i for i, x in enumerate(call_options[:,3]) if x == min_MM]
    min_indices2=call_options[:,3].tolist().index(min_MM)
    min_indice=min_indices[0]
    for i in range(len(call_options)):
        for j in range(len(put_options)):
            if 0 == put_options[j][3]:
                put_options[j][3]=maxMMT
            if 0 == call_options[i][3]:
                call_options[i][3] = maxMMT+1
            call_options[i][4] =  call_options[i][3]/average
            put_options[j][4]= put_options[j][3]/average
    strikesLast=call_options[:,3].tolist()###cange name to all MMt
    Low_MMT = min(strikesLast)
    Index_Newlosest_strike= strikesLast.index(min(strikesLast))
    interested = False 
    EvenIdex=num_strikes
    average_mill = sum(call_options[3:9,3]) / len(call_options[3:9,3])
    interested2 = False 
    if abs(call_options[EvenIdex][0]-price)>abs(call_options[EvenIdex+1][0]-price):
        EvenIdex=num_strikes+1
    if abs(call_options[EvenIdex][0]-price)>abs(call_options[EvenIdex-1][0]-price):
        EvenIdex=num_strikes-1
    if (call_options[EvenIdex][3]>2+Low_MMT) and (call_options[EvenIdex][4]>call_options[Index_Newlosest_strike][4]*7 or call_options[EvenIdex+1][4]>call_options[Index_Newlosest_strike][4]*7) :
        interested = True
    if (average_mill>6*Low_MMT) and (call_options[EvenIdex][4]>call_options[Index_Newlosest_strike][4]*7 or call_options[EvenIdex+1][4]>call_options[Index_Newlosest_strike][4]*7) :
        interested2 = True    
    #################### vbar 
    if(bardisplay==True):
        plt.bar(call_options[:,0], call_options[:,3], width=0.5, label='Call Options')
        
        # Plot the put options
        plt.bar(put_options[:,0], put_options[:,3], width=0.5, label='Put Options')
        
        # Set the x-axis label
        plt.xlabel('Strike Price')
        
        # Set the y-axis label
        plt.ylabel('MM total')
        
        # Set the plot title
        plt.title('Option Chain Open Interest')
        
        # Add a legend
        plt.legend()
        
        # Show the plot
        plt.show()
    #################
    printStuff=False
    if printStuff:    
        print(ticker,": " ,current_price)
        print("done")
        print("method1 ",interested)
        print("method2 ",interested2)
    call_options[:,4]=price
    return(interested,call_options,expirationList[expirationIndex],price)

    #################
    if printStuff: 
        print("Current price: ", current_price)
        print("done")
        print(interested)
        print("method2 ",interested2)
names=["AAPL","ABBV","ABNB","ABT","ADBE","ADI","AFRM","AMAT","AMC","AMD",
       "AMGN","AMZN","AVGO","AXP","BA","BABA","BAC","BIDU","BLK","BMY","C",
       "CAT","CCJ","CCL","CHWY","CL","COIN","COST","CRM","CROX","CRWD","CSCO","CVS",
       "CVX","CZR","DD","DASH","DDOG","DE","DIS","DKNG","DLTR","DOCU","EBAY","ENPH",
       "EWZ","EXPE","F","FANG","FCX","FDX","FL","FSLR","GDX","GE","GLD","GM","GME",
       "GOOG","GOOGL","GS","HD","HON","HOOD","HPQ","HYG","IBM","INTC","iwm","JD","JNJ","JPM",
       "KO","LLY","LMT","LQD","LULU","LUV","M","MA","MCD","MDT","META","MGM","MMM","MO",
       "MRK","MRVL","mrna","MS","MSFT","MSTR","MU","NCLH","NET","NFLX","NKE","NUE","NVDA","OIH",
       "ORCL","PANW","PARA","PEP","PFE","PG","PINS","PLTR","PLUG","PM","PYPL","QCOM","QQQ",
       "RBLX","ROST","RUN","SBUX","SCHW","SHOP","SLV","SMH","SNAP","SNOW",'SPOT',"SOXL",'SOFI', 
       "SPY","SQ",
       "T",'TDOC','TER',"TLT","TSLA","TSM","TTD","TWLO","UAL","UBER","UNH","UNP","UPS","UPST","V","VALE",
       "VZ","WBA","WDC","WFC","WMT","WYNN","X","XBI","XLB","XLF","XLI","XLK","XLRE","XLU",
       "XLV","XLY","XOM","ZM","ZS","vix","qqq","SPY","TAN"]
smallNames=["AAPL","upst","MSFT","ABNB","TTD","ADBE","ADI","AFRM",'GE',
            'NVDA','SNOW','MSTR','BABA','JD','TLT','HYG','V','CRWD','COIN',
            'QCOM','RIVN','MRNA','ZS','HOOD','SHOP','BA','CCJ','TWLO','GOOG','GE',
            'DOCU','PANW','LQD','DKNG','ROKU','WFC','SQ','C','GS','JPM','ZM','U',
            'TSLA','TDOC','NVDA','RBLX','CZR','MGM','FSLR','SOXL','DDOG','F','NET',
            'NCLH','GLD','SLV',"hd","INTC","smh","nke","amd"]
onename=["ADBE","ADI","AFRM",'GE','NVDA','SNOW','MSTR',"xom"]

errorlist=[]
yesnames=[]
pricepoints=[]
start = time.time()
counter=1
Passcheker= False 
chainss=[]
for i in onename:
    print("im scaning ",i)
    try:
        result=screnner(i,False,0 )
        Passcheker=result[0]
        print(result[2])
        if Passcheker :
            chainss.append(result[1])
            yesnames.append(i)
            pricepoints.append(result[3])
            time.sleep(1.8)
            counter=counter+1
    except Exception:
        errorlist.append(i)
        print("errors", i)
        pass
counterforT=-1
end = time.time()
print(end - start)
for T in chainss:
    
    counterforT=counterforT+1
    current_price=pricepoints[counterforT]
    if current_price > 50:
        current_price = round(current_price * 2) / 2
    else:
        current_price = round(current_price * 4) / 4
    #plot the price
    plt.bar(current_price, max(T[:,3])+1, width=0.5, label='price')
    
    plt.bar(T[:,0],T[:,3], width=0.5, label='Call Options')

    # Plot the put options
    plt.bar(T[:,0], T[:,3], width=0.5, label='Put Options',color='darkorange')
    
    
    
    # Set the x-axis label
    plt.xlabel('Strike Price')

    # Set the y-axis label
    plt.ylabel('MM total')

    # Set the plot title
    plt.title('Option Chain Market maker pnl '+yesnames[counterforT] +" price is : "+ str(current_price))
    
    # Add a legend
    plt.legend()

    # Show the plot
    plt.show()
    T[0,4]
print(yesnames)
print("this is |||| erors below")  
print(errorlist) 
plt.clf()  
