import os
import json
from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pandas as pd
from stockList import allStocks
from copy import copy
from updateDB import getStockData, HandleDB, getLastValue, getStockName, getStockIntradayData, updateOHLC, createOHLC

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

def computeIchimoku(d):
    # compute the average variation between points to create new points
    res = np.abs(np.mean((d.index[1:-1] - d.index[0:-2]).to_numpy()))
    minDate = np.datetime64((np.min(d.index)))
    maxDate = np.datetime64((np.max(d.index)))
    for ind in range(1, 26+1):
        d = d.append(pd.Series(name=maxDate + ind * res))
    for ind in range(1, 52+1):
        d = d.append(pd.Series(name=minDate - ind * res))
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
    refDate = (datetime.today() - timedelta(days=days))
    # In case we do not have enought elements
    if len(historyData[historyData.index <= refDate.date()]) == 0:
        return historyData.iloc[-1]['Close']
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

def gentTextOwnStock(dataOut):
    if "netActualGain" in dataOut.index and not np.isnan(dataOut['netActualGain']):
        return ", Net gain : {:.2f} €".format(dataOut['netActualGain']) + ' / ' +  "{:.1f} %".format(dataOut['netActualGainPercent'])
    else:
        return ""
def genText1stock(dataOut):
    return  (
        '/stockinfo' + dataOut['stockname'].replace('.', '_') + ' ' +
        getStockName(dataOut['stockname']) +
        ' var : {:.2f}%'.format(dataOut['var1day'] * 100)) + gentTextOwnStock(dataOut) + '\n'

def checkVar(df, nbDays=1, which='all'):
    nbDaysGetData = nbDays
    strOut = ''
    if nbDays < 4:
        nbDaysGetData = 4
    df = df.copy()
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
def graphEvolutionTitre(stockname):
    data = loadStocks('mystocks.json')
    histData = getStockData(stockname)
    listData = [getValueDays(histData, 30 * months) for months in [12, 6, 3, 1, 1/30, 0]]
    listData = np.array(listData) / listData[0] * 100
    dataFig = []
    dataFig.append({
            'x': ['1 year ago', 'six months ago', 'three months ago', 'last month', 'yesterday', 'now'],
            'y': listData,
            'type': 'bar',
    })
    fig = go.Figure(data=dataFig, layout={'title': stockname + ' Progression du titre sur 1 an'})
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
    return fig
def graphEvolutionIntraday(
    stockname, dateStart=datetime.now() - timedelta(days=1), dateStop=datetime.now() + timedelta(hours=2)
):
    data = getStockIntradayData(stockname)
    data = data[data['timestamp'] > dateStart]
    data = data[data['timestamp'] < dateStop]
    dataFig = []
    dataFig.append({
            'x': data['timestamp'],
            'y': data['price'],
            'type': 'scatter',
    })
    fig = go.Figure(data=dataFig, layout={'title': getStockName(stockname) + ' Intraday'})
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

def graphIchimoku(stockHist):
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
    return dataFig


def graphBougies(stockHist):
    return [{
            'x': stockHist.index,
            'open': stockHist['Open'],
            'high': stockHist['High'],
            'low': stockHist['Low'],
            'close': stockHist['Close'],
            'type': 'candlestick',
            'name': 'candlestick'
    }]

def graphSelfData(stockSerie):
    dataFig = []
    if 'boughtDate' in stockSerie.columns and stockSerie['boughtDate'].notna().values[0]:
        for ind in range(len(stockSerie)):
            xData = [
                stockSerie['boughtDate'].values[ind].astype('M8[D]').astype('O') + timedelta(seconds=1),
                stockSerie['sellDate'].values[ind].astype('M8[D]').astype('O') if stockSerie['sellDate'].notna().values[ind] else datetime.now()
            ]
            yData = [stockSerie['boughtNetValue'].values[ind], stockSerie['boughtNetValue'].values[ind]]
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
    return dataFig


def graphGenericStock(stockSerie, stockHist, stockname=''):
    dataFig = []
    dataFig += graphIchimoku(stockHist)
    dataFig += graphBougies(stockHist)
    if len(stockSerie) > 0:
        dataFig += graphSelfData(stockSerie)
    fig = go.Figure(data=dataFig, layout={
        'title': str(stockname),
        #'xaxis':{'range': [startDate, stopDate]}
    })
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
    return fig

def getTimeDeltaFromSettings(freq=1, unit='D'):
    if unit not in ['T', 'H', 'D', 'W', 'M']:
        return False
    unitDict = {
        'T': timedelta(minutes=1),
        'H': timedelta(hours=1),
        'D': timedelta(days=1),
        'W': timedelta(days=5),
        'M': timedelta(days=31),
    }
    return unitDict[unit] * freq * (52 + 27)


def graphDataForStock(stockname, freq=1, unit='D', histoDepth=timedelta(days=60)):
    df = loadStocks('mystocks.json')
    if unit in ['T', 'H']:
        historyData = getStockIntradayData(stockname)
        historyData = createOHLC(historyData, freq=freq, unit=unit)
    else:
        historyData = getStockData(stockname)
        historyData = updateOHLC(historyData, freq=freq, unit=unit)
    if len(historyData) > 0:
        startDate=datetime.now() - histoDepth
        historyData = historyData[historyData.index > startDate - getTimeDeltaFromSettings(freq, unit)]
        print(getTimeDeltaFromSettings(freq, unit))
        histo = computeIchimoku(historyData)
        histo = histo[histo.index > startDate]
        return graphGenericStock(df[(df['stockname'] == stockname) & (df['boughtDate'] > datetime.now() - histoDepth)], histo, stockname=stockname)
    else:
        return None