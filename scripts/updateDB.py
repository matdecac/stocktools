import os
import json
import time
import logging
from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd
from libs.datamodel import StockDay, StockIntraDay, HistDetectStockVar
from sqlalchemy import create_engine, desc, asc
from sqlalchemy.orm import scoped_session, sessionmaker
import yfinance as yf
from yahoo_fin import stock_info as si


def isMarketOpen(market='PA'): 
    import pytz
    def utc2local(utc_dt, local_tz=pytz.timezone('Europe/Paris')):
        local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
        return local_tz.normalize(local_dt) # .normalize might be unnecessary
    

    nowTime =  utc2local(datetime.today().replace(hour=datetime.today().hour))
    if market == 'PA':
        openM =  utc2local(datetime.today().replace(hour=7, minute=55, second=0))
        closeM =  utc2local(datetime.today().replace(hour=16, minute=40, second=0))
    elif market == 'NY':
        openM =  utc2local(datetime.today().replace(hour=9+5, minute=30, second=0))
        closeM =  utc2local(datetime.today().replace(hour=16+5, minute=0, second=0))
    else:
        logging.error('Market: ' + str(market) + ' do not exist')
        return False
    if nowTime > openM and nowTime < closeM and nowTime.weekday() in [0, 1, 2, 3, 4]:
        return True
    else:
        return False

def addBoughtLine(msgText):
    df = pd.read_json('stockprospects.json', orient='index')
    listStockNamesJSON = [df.loc[ind]['stockname'] for ind in df.index]

    splited = msgText.split(' ')
    valName = splited[1]
    value = splited[2]
    qty = splited[3]
    jsonToUpdate = 'mystocks.json'
    if valName in listStockNamesJSON:
        df = pd.read_json(jsonToUpdate, orient='index')
        df= df.append({
            'stockname': valName, 
            'boughtDate': datetime.today(), 
            'boughtValue': float(value),
            'boughtQ': float(qty),
            'boughtFrais': 1.99,
            'name': getStockName(valName),
            'sellFrais': 1.99,
        }, ignore_index=True)
        df.to_json(jsonToUpdate, orient='index', indent=4)
        return "Action rajouté."
    else:
        return "Action inconnu, ajout avec /stockinfo" + valName.replace('.', '_')

def addSoldLine(msgText):
    df = pd.read_json('mystocks.json', orient='index')
    listStockNamesJSON = [df.loc[ind]['stockname'] for ind in df.index]

    splited = msgText.split(' ')
    valName = splited[1]
    value = splited[2]
    jsonToUpdate = 'mystocks.json'
    if valName in listStockNamesJSON:
        df = pd.read_json(jsonToUpdate, orient='index')
        df.loc[df[df['stockname'] == valName].iloc[-1].name, 'sellValue'] = float(value)
        df.loc[df[df['stockname'] == valName].iloc[-1].name, 'sellDate'] = datetime.today()
        df.to_json(jsonToUpdate, orient='index', indent=4)
        return "Action vendu."
    else:
        return "Action inconnu, ajout avec /stockinfo" + valName.replace('.', '_')

def checkMissingStock():
    jsonToUpdate = 'mystocks.json'
    df = pd.read_json(jsonToUpdate, orient='index')
    jsonToUpdate = 'stockprospects.json'
    df2 = pd.read_json(jsonToUpdate, orient='index')
    for stockname in list(set(df['name']).difference(df2['name'])):
        addStock(stockname)

def getStockName(stockname):
    df = pd.read_json('stockprospects.json', orient='index')
    return str(df[df['stockname'] == stockname]['name'].iloc[0])

def searchFullName(stockName):
    try:
        return yf.Ticker(stockName).info['shortName']
    except:
        return np.NaN

def fillNameFromYF(df):
    if 'name' in df.columns:
        df.loc[df['name'].isna(), 'name'] = df[df['name'].isna()]['stockname'].apply(lambda x : searchFullName(x))
    else:
        df['name'] = df['stockname'].apply(lambda x : searchFullName(x))
    return df

def addStock(newStockname, jsonToUpdate='stockprospects.json'):
    df = pd.read_json(jsonToUpdate, orient='index')
    listStockNamesJSON = [df.loc[ind]['stockname'] for ind in df.index]
    if (
        newStockname not in listStockNamesJSON and
        len(getYFdata(newStockname, startDate=datetime.now()-timedelta(days=5))) > 0
    ):
        df = df.append({'stockname': newStockname}, ignore_index=True)
        df = fillNameFromYF(df)
        df.to_json(jsonToUpdate, orient='index', indent=4)
        updateDB(daysHisto=365*5)
        updateDB(daysHisto=6, stockRes='intraday')
        return True
    else:
        return False

def ohlcFromDFparms(test, openC, highC, lowC, closeC, adfCloseC):
    if len(test) > 0:
        return pd.Series({
            'Open': test.iloc[0][openC],
            'High': np.max(test[highC]),
            'Low': np.min(test[lowC]),
            'Close': test.iloc[-1][closeC],
            'Adj Close': test.iloc[-1][adfCloseC],
        })
    else:
        return pd.Series({
            'Open': None,
            'High': None,
            'Low': None,
            'Close': None,
            'Adj Close': None,
        })
def ohlcFromOHLCdf(test):
    return ohlcFromDFparms(test, 'Open', 'High', 'Low', 'Close', 'Adj Close')

def updateOHLC(df, freq=5, unit='T'):
    if len(df) == 0:
        return df
    #assert (len(df) > 0), "Len of DF is 0"
    if unit not in ['T', 'H', 'D', 'W', 'M']:
        logging.error('unit ' + str(unit) + ' not allowed')
        return df
    df.index = df.index.astype('M8[ns]') + timedelta(seconds=1)
    newDF = df.sort_index().groupby(pd.Grouper(freq=str(freq)+str(unit))).apply(ohlcFromOHLCdf)
    newDF.index = newDF.index.to_pydatetime()
    return newDF.dropna()

def prepareStockData(df):
    df = df.rename(columns={
        "stockname": "stockname",
        "timestamp": "timestamp",
        "priceOpen": "Open",
        "priceHigh": "High",
        "priceLow": "Low",
        "priceClose": "Close",
        "priceAdjClose": "Adj Close",
        "volume": "Volume",
    })
    df.index = df['timestamp']
    return df

def checkSendMessage(stockName, message_type, timestamp=datetime.now() - timedelta(minutes=30)):
    handleDB = HandleDB()
    
    result = handleDB.session.query(
        HistDetectStockVar
    ).filter(
        HistDetectStockVar.stockname==stockName
    ).filter(
        HistDetectStockVar.timestamp >= timestamp
    ).filter(
        HistDetectStockVar.dataorigin == message_type
    ).order_by(desc(HistDetectStockVar.timestamp)).all()
    if len(result) == 0:
        histDetect = HistDetectStockVar()
        histDetect.stockname = stockName
        histDetect.dataorigin = message_type
        histDetect.timestamp = datetime.now()
        handleDB.session.add(histDetect)
        handleDB.session.commit()
        handleDB.session.close()
        return True
    return False

def getStockIntradayData(stockname, sinceTime=datetime.now() - timedelta(days=10)):
    handleDB = HandleDB()
    queryData = handleDB.session.query(
        StockIntraDay
    ).filter(
        StockIntraDay.stockname==stockname
    ).filter(
        StockIntraDay.timestamp >= sinceTime
    ).order_by(desc(StockIntraDay.timestamp))
    df = pd.read_sql(queryData.statement, handleDB.engine)
    handleDB.close()
    df = prepareStockData(df)
    return df

def getStockData(stockname):
    addStock(stockname)
    handleDB = HandleDB()
    queryData = handleDB.session.query(StockDay).filter(StockDay.stockname==stockname).order_by(desc(StockDay.timestamp))
    df = pd.read_sql(queryData.statement, handleDB.engine)
    handleDB.close()
    df = prepareStockData(df)
    return df

def getLastsValue(stockname, ptAskedL=[14]):
    handleDB = HandleDB()
    values = {}
    try:
        values[0] = (handleDB.session.query(StockIntraDay).filter(
                StockIntraDay.stockname==stockname
        ).order_by(desc(StockIntraDay.timestamp)).first().priceClose)
    except:
        pass
    for ptAsked in ptAskedL:
        ptAskedTD = datetime.now() - timedelta(minutes=ptAsked)
        try:
            values[ptAsked] = (
                handleDB.session.query(
                    StockIntraDay
                ).filter(
                    StockIntraDay.stockname==stockname
                ).filter(
                    StockIntraDay.timestamp >= ptAskedTD
                ).order_by(asc(StockIntraDay.timestamp)).first().priceClose
            )
        except:
            pass
    handleDB.close()
    return values


def getLastValue(stockname):
    handleDB = HandleDB()
    value = handleDB.session.query(StockIntraDay).filter(StockIntraDay.stockname==stockname).order_by(desc(StockIntraDay.timestamp)).first()
    if value is None:
        value = handleDB.session.query(StockDay).filter(StockDay.stockname==stockname).order_by(desc(StockDay.timestamp)).first()
    handleDB.close()
    return value.priceClose

class HandleDB():
    def __init__(self, dbname='sqlite:///stockdb.db'):
        self.engine = create_engine(dbname, echo=False)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    def close(self):
        self.session.close()

def getYFdata(listStockNames, startDate, interval="1m"):
    return yf.download(
        listStockNames,
        start=startDate,
        end=datetime.now()+timedelta(days=1), 
        interval=interval,
        progress=False,
        group_by="ticker"
    )

def updateDBintradayFromSSI():
    df = pd.read_json('stockprospects.json', orient='index')
    listStockNames = [df.loc[ind]['stockname'] for ind in df.index]
    start_time = time.time()
    stockval = {}
    for stockname in listStockNames:
        upVal = False
        if '.PA' in stockname:
            if isMarketOpen('PA'):
                upVal = True
        #elif '-EUR' in stockname:
        #        upVal = True
        #else: # SUPPOSE US VALUE
        #    if (
        #        datetime.today().weekday() in [0, 1, 2, 3, 4] and 
        #        datetime.today().hour - 5 >= 9 and datetime.today().hour - 5 <= 18
        #    ): 
        #        upVal = True
        if upVal:
            try:
                stockval[stockname] = si.get_live_price(stockname)
            except:
                logging.warn( "Value for " + stockname + " failed to be grabbed")
               
    handleDB = HandleDB()
    for stockname, value in stockval.items():
        stockIntraDay = StockIntraDay()
        stockIntraDay.stockname = stockname
        stockIntraDay.timestamp = datetime.now()
        stockIntraDay.dateadded = datetime.now()
        stockIntraDay.priceOpen = value
        stockIntraDay.priceHigh = value
        stockIntraDay.priceLow = value
        stockIntraDay.priceClose = value
        stockIntraDay.priceAdjClose = value
        handleDB.session.add(stockIntraDay)
        handleDB.session.commit()
        logging.debug('Update for ' + stockname + ' value : {:.2f} €'.format(value))
    handleDB.session.close()
    logging.info("Intraday update in %s seconds" % (time.time() - start_time))

def updateDB(daysHisto=1, stockRes='daily'):
    logger = logging.getLogger()
    start_time = time.time()
    dateStart = datetime.now() - timedelta(days=daysHisto)
    df = pd.read_json('stockprospects.json', orient='index')
    listStockNames = [df.loc[ind]['stockname'] for ind in df.index]
    if stockRes == 'intraday':
        StockObj = StockIntraDay
        df = getYFdata(listStockNames, dateStart, interval="1m")
    else:
        StockObj = StockDay
        df = getYFdata(listStockNames, dateStart, interval="1d")
    historyData = []
    for stockname in listStockNames:
        historyData.append(df[stockname][
            (df[stockname]['Open'].notna()) | 
            (df[stockname]['High'].notna()) | 
            (df[stockname]['Low'].notna()) | 
            (df[stockname]['Close'].notna())
        ].fillna(method='ffill'))
    for ind in range(len(listStockNames)):
        historyData[ind] = historyData[ind][historyData[ind]['Open'].notna()]
        historyData[ind]['stockname'] = listStockNames[ind]
        historyData[ind]['timestamp'] = historyData[ind].index
        historyData[ind] = historyData[ind].rename(columns={
            "stockname": "stockname",
            "timestamp": "timestamp",
            "Open": "priceOpen",
            "High": "priceHigh",
            "Low": "priceLow",
            "Close": "priceClose",
            "Adj Close": "priceAdjClose",
            "Volume": "volume",
        })
        historyData[ind]['dateadded'] = datetime.now()
    handleDB = HandleDB()
    for ind in range(len(listStockNames)):
        if len(historyData[ind]) > 0:
            dataRes = handleDB.session.query(StockObj).filter(
                StockObj.stockname==listStockNames[ind]
            ).filter(
                StockObj.timestamp >= historyData[ind].iloc[0].name
            ).filter(
                StockObj.timestamp <= historyData[ind].iloc[-1].name
            ).delete()
        else:
            logging.info("No data to add for : " + listStockNames[ind])
        

    for ind in range(len(listStockNames)):
        if len(historyData[ind]) > 0:
            output = historyData[ind].to_dict('records')
            handleDB.session.bulk_insert_mappings(StockObj, output)
            handleDB.session.commit()
    handleDB.session.close()
    logging.info("Daily update in %s seconds" % (time.time() - start_time))



