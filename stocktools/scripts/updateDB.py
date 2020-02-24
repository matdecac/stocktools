import os
import json
import time
import logging
from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd
from libs.datamodel import StockDay, StockIntraDay
from sqlalchemy import create_engine, desc, asc
from sqlalchemy.orm import scoped_session, sessionmaker
import yfinance as yf
from yahoo_fin import stock_info as si


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
            if (
                datetime.today().weekday() in [0, 1, 2, 3, 4] and 
                datetime.today().hour + 1 >= 9 and datetime.today().hour + 1 <= 18
            ):
                upVal = True
        elif '-EUR' in stockname:
                upVal = True
        else: # SUPPOSE US VALUE
            if (
                datetime.today().weekday() in [0, 1, 2, 3, 4] and 
                datetime.today().hour - 5 >= 9 and datetime.today().hour - 5 <= 18
            ): 
                upVal = True
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
        dataRes = handleDB.session.query(StockObj).filter(
            StockObj.stockname==listStockNames[ind]
        ).filter(
            StockObj.timestamp >= historyData[ind].iloc[0].name
        ).filter(
            StockObj.timestamp <= historyData[ind].iloc[-1].name
        ).delete()

    for ind in range(len(listStockNames)):
        output = historyData[ind].to_dict('records')
        handleDB.session.bulk_insert_mappings(StockObj, output)
        handleDB.session.commit()
    handleDB.session.close()
    logging.info("Daily update in %s seconds" % (time.time() - start_time))



