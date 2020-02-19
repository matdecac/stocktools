import os
import json
from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd
from libs.datamodel import StockDay, StockIntraDay
from sqlalchemy import create_engine, desc, asc
from sqlalchemy.orm import scoped_session, sessionmaker
import yfinance as yf

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

def addStock(newStockname, jsonToUpdate='stockprospects.json'):
    df = pd.read_json(jsonToUpdate, orient='index')
    listStockNamesJSON = [df.loc[ind]['stockname'] for ind in df.index]
    if newStockname not in listStockNamesJSON:
        df = df.append({'stockname': newStockname}, ignore_index=True)
        df = fillNameFromYF(df)
        df.to_json(jsonToUpdate, orient='index', indent=4)
        updateDB(daysHisto=365*5)
        return True
    else:
        return False

def getStockData(stockname):
    addStock(stockname)
    handleDB = HandleDB()
    queryData = handleDB.session.query(StockDay).filter(StockDay.stockname==stockname).order_by(desc(StockDay.datestamp))
    df = pd.read_sql(queryData.statement, handleDB.engine)
    handleDB.close()
    df = df.rename(columns={
        "stockname": "stockname",
        "datestamp": "datestamp",
        "priceOpen": "Open",
        "priceHigh": "High",
        "priceLow": "Low",
        "priceClose": "Close",
        "priceAdjClose": "Adj Close",
        "volume": "Volume",
    })
    df.index = df['datestamp']
    return df

def getStockIntradayData(stockname):
    handleDB = HandleDB()
    queryData = handleDB.session.query(StockIntraDay).filter(StockDay.stockname==stockname).order_by(desc(StockDay.datestamp))
    df = pd.read_sql(queryData.statement, handleDB.engine)
    handleDB.close()
    return df


def getLastValue(stockname):
    addStock(stockname)
    handleDB = HandleDB()
    value = handleDB.session.query(StockDay).filter(StockDay.stockname==stockname).order_by(desc(StockDay.datestamp)).first().priceClose
    handleDB.close()
    return value



class HandleDB():
    def __init__(self, dbname='sqlite:///stockdb.db'):
        self.engine = create_engine(dbname, echo=False)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    def close(self):
        self.session.close()

def updateDB(daysHisto=10):
    df = pd.read_json('stockprospects.json', orient='index')
    listStockNames = [df.loc[ind]['stockname'] for ind in df.index]

    startDate=date.today() - timedelta(days=daysHisto)
    stopDate=date.today() + timedelta(days=1)

    allStocksHist = yf.download(
        listStockNames,
        start=startDate, 
        end=stopDate, 
        progress=False,
        group_by="ticker"
    )

    historyData = []
    for ind in range(len(listStockNames)):
        if len(listStockNames) > 1:
            historyData.append(allStocksHist[listStockNames[ind]].fillna(method='ffill'))
        else:
            historyData.append(allStocksHist.fillna(method='ffill'))

    for ind in range(len(listStockNames)):
        historyData[ind] = historyData[ind][historyData[ind]['Open'].notna()]
        historyData[ind]['stockname'] = listStockNames[ind]
        historyData[ind]['datestamp'] = historyData[ind].index
        historyData[ind] = historyData[ind].rename(columns={
            "stockname": "stockname",
            "datestamp": "datestamp",
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
        dataRes = handleDB.session.query(StockDay).filter(StockDay.stockname==listStockNames[ind]).order_by(desc(StockDay.datestamp)).first()
        if dataRes is not None:
            historyData[ind] = historyData[ind][historyData[ind]['datestamp'] >= np.datetime64(dataRes.datestamp)]
            if len(historyData[ind]) > 0:
                handleDB.session.delete(dataRes)
                handleDB.session.commit()
        else:
            historyData[ind]
        #display(historyData[ind])
    for ind in range(len(listStockNames)):
        output = historyData[ind].to_dict('records')
        handleDB.session.bulk_insert_mappings(StockDay, output)
        handleDB.session.commit()
    handleDB.session.close()
    handleDB = HandleDB()
    for ind in range(len(listStockNames)):
        dataRes = handleDB.session.query(StockDay).filter(StockDay.stockname==listStockNames[ind]).order_by(desc(StockDay.datestamp)).first()
        stockIntraDay = StockIntraDay()
        stockIntraDay.stockname = dataRes.stockname
        stockIntraDay.timestamp = dataRes.datestamp
        stockIntraDay.dateadded = datetime.now()
        stockIntraDay.price = dataRes.priceClose
        handleDB.session.add(stockIntraDay)
    handleDB.session.close()


