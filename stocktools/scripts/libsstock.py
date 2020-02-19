import os
import json
from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pandas as pd
from stockList import allStocks
from copy import copy
from updateDB import getStockData, HandleDB, getLastValue, getStockName

def loadStocks(jsonFile):
    df = pd.read_json(jsonFile, orient='index')
    df['valueNow'] = df['stockname'].apply(lambda x : getLastValue(x))
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
        if 'sellDate' in df.columns:
            df['sellDate'] = pd.to_datetime(df['sellDate'], unit='ms')
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

def computeIchimoku(d):
    minDate = np.min(d.index)
    maxDate = np.max(d.index)
    for ind in range(1, 26+1):
        d = d.append(pd.Series(name=maxDate + timedelta(days=ind)))
    for ind in range(1, 52+1):
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
    #print(historyData)
    #pdb.set_trace()
    result = historyData.iloc[historyData.index.get_loc(datetime.today() - timedelta(days=days),method='backfill')]
    #
    return result['Close']
def computeVar(dfSerie, histData, refDay=1):
    return getValueDays(histData, 0) / getValueDays(histData, refDay) - 1.0
def checkVarPos(dfSerie, histData, refDay=1, percentVar=0.05):
    return computeVar(dfSerie, histData, refDay) > percentVar
def checkVarNeg(dfSerie, histData, refDay=1, percentVar=-0.05):
    return computeVar(dfSerie, histData, refDay) < percentVar
def computeVarAndStatus(df, historyData, refDay=1, percentVarNeg=-0.05, percentVarPos=0.05):
    for ind in range(len(df)):
        historyData = getStockData(df.iloc[ind]['stockname'])
        df.loc[df['stockname'] == df.iloc[ind]['stockname'], 'var1Neg'] = checkVarNeg(df.iloc[ind], historyData, refDay, percentVarNeg)
        df.loc[df['stockname'] == df.iloc[ind]['stockname'], 'var1Pos'] = checkVarPos(df.iloc[ind], historyData, refDay, percentVarPos)
        df.loc[df['stockname'] == df.iloc[ind]['stockname'], 'var1day'] = computeVar(df.iloc[ind], historyData, refDay)
    return df


def genText1stock(dataOut):
    return  ('/stockinfo' + dataOut['stockname'].replace('.', '_') + ' ' + getStockName(dataOut['stockname']) + ' var : {:.2f}%'.format(dataOut['var1day'] * 100)) + '\n'
def checkVar(df, nbDays=1, which='all'):
    nbDaysGetData = nbDays
    strOut = ''
    if nbDays < 4:
        nbDaysGetData = 4
    df = df.copy()
    df = df.drop_duplicates(subset='stockname')
    if 'all' == which:
        for data in computeVarAndStatus(df, nbDays).sort_values('var1day').index:
            dataOut = df.loc[data]
            strOut += genText1stock(dataOut)
    elif 'neg' == which:
        for data in df[computeVarAndStatus(df, nbDays).sort_values('var1day')['var1Neg']].index:
            dataOut = df.loc[data]
            strOut += genText1stock(dataOut)
    elif 'pos' == which:
        for data in df[computeVarAndStatus(df, nbDays).sort_values('var1day')['var1Pos']].index:
            dataOut = df.loc[data]
            strOut += genText1stock(dataOut)
    return (strOut, df)
def graphEvolutionTitre(histData, data):
    listData = [getValueDays(histData, 30 * months) for months in [12, 6, 3, 1, 1/30, 0]]
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
def graphRendement(df, method='sold'):
    selection = (df['boughtValue'].notna())
    if method == 'sold':
        selection = (df['sellDate'].notna() & selection) == False
    listData = list(df[selection]['netActualGain'])
    listData.append(df[selection]['netActualGain'].sum())
    xData = [df.loc[ind]['name'] + '\n' + '{:.2f} €'.format(df.loc[ind]['netActualGain']) for ind in df[selection].index]
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

def graphIchimoku(stockSerie, stockHist, startDate=datetime.now() - timedelta(days=365), stopDate=datetime.now() + timedelta(days=31)):
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
    fig = go.Figure(data=dataFig, layout={
        'title': str(stockSerie['name'].iloc[0]),
        #'xaxis':{'range': [startDate, stopDate]}
    })
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
    
    return fig
