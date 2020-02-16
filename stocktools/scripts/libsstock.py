import os
import json
from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
from yahoo_fin import stock_info as si
from stockList import allStocks
from copy import copy

def getLiveValue(stockName):
    return si.get_live_price(stockName)

def loadStocks(jsonFile):
    df = pd.read_json(jsonFile, orient='index')
    df['valueNow'] = df['stockname'].apply(lambda x : getLiveValue(x))
    if 'boughtValue' in df.columns:
        selectBought = (df['boughtValue'].notna())
        df.loc[selectBought, 'boughtDate'] = pd.to_datetime(df[selectBought]['boughtDate'], unit='ms')
        selectSold = (df['sellDate'].notna() & selectBought)
        selectBoughtNotSold = (selectBought & selectSold == False)
        df.loc[selectBought, 'boughtNetValue'] = (
            df[selectBought]['boughtValue'] + (df[selectBought]['boughtFrais'] + df[selectBought]['sellFrais'])/df[selectBought]['boughtQ']
        )
        df.loc[selectSold, 'netActualGain'] = (
            (df[selectSold]['sellValue'] - df[selectSold]['boughtNetValue'])
        )
        df.loc[selectBoughtNotSold, 'netActualGain'] = (
            (df[selectBoughtNotSold]['valueNow'] - df[selectBoughtNotSold]['boughtNetValue'])
        )
        df['netActualGain'] = df['netActualGain'] * df['boughtQ']
        df.loc[selectBought, 'netActualGainPercent'] = (
            (df[selectBought]['netActualGain'])/df[selectBought]['boughtNetValue']/df['boughtQ']
        )
        df['netActualGainPercent'] = df['netActualGainPercent']*100
        df.loc[selectSold, 'netActualLock'] = 0.0
        df.loc[selectBoughtNotSold, 'netActualLock'] = df[selectBoughtNotSold]['valueNow'] * df[selectBoughtNotSold]['boughtQ']
    return df

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

def getYFdate(df, startDate=date.today() - timedelta(days=365+41), stopDate=date.today()):
    listStockNames = [df.loc[ind]['stockname'] for ind in df.index]

    allStocksHist = yf.download(
        listStockNames,
        start=startDate, 
        end=stopDate, 
        progress=False,
        group_by="ticker"
    )
    
    stockData = []
    for ind in range(len(listStockNames)):
        if len(listStockNames) > 1:
            stockData.append(allStocksHist[listStockNames[ind]].fillna(method='ffill'))
        else:
            stockData.append(allStocksHist.fillna(method='ffill'))
        #stock['info'] = stock['ticker'].info
    return stockData

def computeIchimoku(d):
    minDate = d.index[0]
    maxDate = d.index[-1]
    for ind in range(1, 52+1):
        d = d.append(pd.Series(name=maxDate + timedelta(days=ind)))
    for ind in range(1, 26+1):
        d = d.append(pd.Series(name=minDate - timedelta(days=ind)))
    d = d.sort_index()
    # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2))
    nine_period_high = d['High'].rolling(window= 9).max()
    nine_period_low = d['Low'].rolling(window= 9).min()
    d.loc[:, 'tenkan_sen'] = (nine_period_high + nine_period_low) /2

    # Kijun-sen (Base Line): (26-period high + 26-period low)/2))
    period26_high = d['High'].rolling(window=26).max()
    period26_low = d['Low'].rolling(window=26).min()
    d.loc[:, 'kijun_sen'] = (period26_high + period26_low) / 2
    # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2))
    d.loc[:, 'senkou_span_a'] = ((d['tenkan_sen'] + d['kijun_sen']) / 2).shift(26)

    # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2))
    period52_high = d['High'].rolling(window=52).max()
    period52_low = d['Low'].rolling(window=52).min()
    d.loc[:, 'senkou_span_b'] = ((period52_high + period52_low) / 2).shift(26)

    # The most current closing price plotted 26 time periods behind (optional)
    d.loc[:, 'chikou_span'] = d['Close'].shift(-26)

    d.loc[:, 'senkou_span_pos'] = d['senkou_span_a'] > d['senkou_span_b']
    return d

def getValueDays(historyData, days):
    result = historyData.iloc[historyData.index.get_loc(datetime.today() - timedelta(days=days),method='nearest')]
    return np.mean([result['Close'], result['Open']])
def computeVar(dfSerie, histData, refDay=1):
    return dfSerie['valueNow'] / getValueDays(histData, refDay) - 1.0
def checkVarPos(dfSerie, histData, refDay=1, percentVar=0.05):
    return computeVar(dfSerie, histData, refDay) > percentVar
def checkVarNeg(dfSerie, histData, refDay=1, percentVar=-0.05):
    return computeVar(dfSerie, histData, refDay) < percentVar
def computeVarAndStatus(df, historyData, refDay=1, percentVarNeg=-0.05, percentVarPos=0.05):
    for ind in range(len(df)):
        df.loc[df['stockname'] == df.iloc[ind]['stockname'], 'var1Neg'] = checkVarNeg(df.iloc[ind], historyData[ind], refDay, percentVarNeg)
        df.loc[df['stockname'] == df.iloc[ind]['stockname'], 'var1Pos'] = checkVarPos(df.iloc[ind], historyData[ind], refDay, percentVarPos)
        df.loc[df['stockname'] == df.iloc[ind]['stockname'], 'var1day'] = computeVar(df.iloc[ind], historyData[ind], refDay)
    return df
def checkVar(nbDays=1, fileJson='mystocks.json'):
    strOut = ''
    df = loadStocks(fileJson)
    historyData = getYFdate(df, startDate=date.today() - timedelta(days=nbDays+1), stopDate=date.today() + timedelta(days=1))
    for data in df[computeVarAndStatus(df, historyData, nbDays)['var1Neg']].index:
        dataOut = df.loc[data]
        strOut += (dataOut['name'] + ' var : {:.2f}%'.format(dataOut['var1day'] * 100)) + '\n'
    for data in df[computeVarAndStatus(df, historyData, nbDays)['var1Pos']].index:
        dataOut = df.loc[data]
        strOut += (dataOut['name'] + ' var : {:.2f}%'.format(dataOut['var1day'] * 100)) + '\n'
    return (strOut, df, historyData)

def graphEvolutionTitre(histData, data):
    listData = [getValueDays(histData, 30 * months) for months in [12, 6, 3, 1, 1/30]] + [data['valueNow']]
    listData = np.array(listData) / listData[0] * 100
    dataFig = []
    dataFig.append({
            'x': ['1 year ago', 'six months ago', 'three months ago', 'last month', 'yesterday', 'now'],
            'y': listData,
            'type': 'bar',
    })
    fig = go.Figure(data=dataFig, layout={'title': data['name'] + ' Progression du titre sur 1 an'})
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
    return fig

def graphBestGain(df):
    dataFig = []
    dataFig.append({
            'labels': df['name'],
            'values': df['netActualGain'],
            'text': [df.loc[ind]['name'] + '\n' + '{:.2f} €'.format(df.loc[ind]['netActualGain']) for ind in df.index],
            'type': 'pie',
            'textinfo':'text'
    })
    fig = go.Figure(data=dataFig, layout={'title': 'Best rendement'})
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
    return fig
def graphWorseGain(df):
    dataFig = []
    dataFig.append({
            'labels': df['name'],
            'values': - df['netActualGain'],
            'text': [df.loc[ind]['name'] + '\n' + '{:.2f} €'.format(df.loc[ind]['netActualGain']) for ind in df.index],
            'type': 'pie',
            'textinfo':'text'
    })
    fig = go.Figure(data=dataFig, layout={'title': 'Worse rendement'})
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
    return fig
def graphCashLock(df):
    dataFig = []
    dataFig.append({
            'labels': df['name'],
            'values': df['netActualLock'],
            'text': [df.loc[ind]['name'] + '\n' + '{:.2f} €'.format(df.loc[ind]['netActualLock']) for ind in df.index],
            'type': 'pie',
            'textinfo':'text'
    })
    fig = go.Figure(data=dataFig, layout={'title': 'Cash repartition'})
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
    return fig
def graphRendement(df):
    selectBought = (df['boughtValue'].notna())
    selectSold = (df['sellDate'].notna() & selectBought) == False
    listData = list(df[selectSold]['netActualGain'])
    listData.append(df[selectSold]['netActualGain'].sum())
    xData = [df.loc[ind]['name'] + '\n' + '{:.2f} €'.format(df.loc[ind]['netActualGain']) for ind in df[selectSold].index]
    xData.append('Somme : {:.2f} €'.format(listData[-1]))
    dataFig = []
    dataFig.append({
            'x': xData,
            'y': listData,
            'type': 'bar',
    })
    fig = go.Figure(data=dataFig, layout={'title': 'Rendement'})
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
    return fig

def graphIchimoku(stockSerie, stockHist):
    d = stockHist
    dataFig = []
    custom = d.copy()
    custom.loc[custom['senkou_span_pos'], 'senkou_span_a_pos'] = custom['senkou_span_a'][custom['senkou_span_pos']]
    custom.loc[custom['senkou_span_pos'], 'senkou_span_b_pos'] = custom['senkou_span_b'][custom['senkou_span_pos']]
    custom.loc[custom['senkou_span_pos'] != True, 'senkou_span_a_pos'] = custom['senkou_span_a'][custom['senkou_span_pos'] != True]
    custom.loc[custom['senkou_span_pos'] != True, 'senkou_span_b_pos'] = custom['senkou_span_a'][custom['senkou_span_pos'] != True]
    custom.loc[custom['senkou_span_pos'] != True, 'senkou_span_a_neg'] = custom['senkou_span_a'][custom['senkou_span_pos'] != True]
    custom.loc[custom['senkou_span_pos'] != True, 'senkou_span_b_neg'] = custom['senkou_span_b'][custom['senkou_span_pos'] != True]
    custom.loc[custom['senkou_span_pos'], 'senkou_span_a_neg'] = custom['senkou_span_b'][custom['senkou_span_pos']]
    custom.loc[custom['senkou_span_pos'], 'senkou_span_b_neg'] = custom['senkou_span_b'][custom['senkou_span_pos']]

    dataFig.append({
        'y': custom['senkou_span_a_pos'], 'x':custom['senkou_span_a_pos'].index, 
        'name': 'senkou_span_a', 'opacity': 0.4, 'line': {'width':1.0, 'color': 'blue'}
    })
    dataFig.append({
        'y': custom['senkou_span_b_pos'], 'x':custom['senkou_span_b_pos'].index, 
        'name': 'senkou_span_b', 'opacity': 0.4, 'line': {'width':1.0, 'color': 'blue'}, 'fill':'tonextx'
    })
    dataFig.append({
        'y': custom['senkou_span_a_neg'], 'x':custom['senkou_span_a_neg'].index, 
        'name': 'senkou_span_a', 'opacity': 0.4, 'line': {'width':1.0, 'color': 'orange'}
    })
    dataFig.append({
        'y': custom['senkou_span_b_neg'], 'x':custom['senkou_span_b_neg'].index, 
        'name': 'senkou_span_b', 'opacity': 0.4, 'line': {'width':1.0, 'color': 'orange'}, 'fill':'tonextx'
    })
    dataFig.append({
        'y': custom['senkou_span_a'], 'x':custom['senkou_span_a'].index, 
        'name': 'senkou_span_a', 'opacity': 1.0, 'line': {'width':1.0, 'color': 'blue'}
    })
    dataFig.append({
        'y': custom['senkou_span_b'], 'x':custom['senkou_span_b'].index, 
        'name': 'senkou_span_a', 'opacity': 1.0, 'line': {'width':1.0, 'color': 'orange'}
    })
    for serieN in ['tenkan_sen', 'kijun_sen', 'chikou_span']:
        dataFig.append(
            {'y': d[serieN], 'x':d.index, 'name': serieN, 'opacity': 1, 'line': {'width':1}}
        )


    dataFig.append({
            'x': d.index,
            'open': d['Open'],
            'high': d['High'],
            'low': d['Low'],
            'close': d['Close'],
            'type': 'candlestick',
            'name': 'candlestick'
    })
    if 'boughtDate' in stockSerie.columns and stockSerie['boughtDate'].notna().values[0]:
        xData = [
            stockSerie['boughtDate'].values[0].astype('M8[D]').astype('O'),
            stockSerie['sellDate'].values[0] if stockSerie['sellDate'].notna().values[0] else np.datetime64('now')
        ]
        yData = [stockSerie['boughtNetValue'].values[0], stockSerie['boughtNetValue'].values[0]]
        dataFig.append({
            'x': xData, 
            'y': yData, 
            'name': 'Gain barrier', 'type': 'scatter', 'mode': 'lines'
        })
        dataFig.append({
            'x': stockSerie['boughtDate'], 
            'y': stockSerie['boughtValue'], 
            'name': 'Buy In', 'type': 'scatter', 'mode': 'markers',
            'marker': dict(
                color='yellow',
                size=10,
                line=dict(
                    color='orange',
                    width=3
                )
            ),
        })
    if 'sellDate' in stockSerie.columns and stockSerie['sellDate'].notna().values[0]:
        dataFig.append({
            'x': stockSerie['sellDate'], 
            'y': stockSerie['sellValue'], 
            'name': 'Sell', 'type': 'scatter', 'mode': 'markers',
            'marker': dict(
                color='orange',
                size=10,
                line=dict(
                    color='yellow',
                    width=3
                )
            ),
        })
    fig = go.Figure(data=dataFig, layout={'title': str(stockSerie['name'].iloc[0])})
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
    
    return fig