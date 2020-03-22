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

def getYFdate(stockList, startDate=date.today() - timedelta(days=365+41), stopDate=date.today()):
    listStockNames = [stock['stockname'] for stock in stockList]

    allStocksHist = yf.download(
        listStockNames,
        start=startDate, 
        end=stopDate, 
        progress=False,
        group_by="ticker"
    )

    for stock in stockList:
        if len(stockList) > 1:
            stock['history'] = allStocksHist[stock['stockname']].fillna(method='ffill')
        else:
            stock['history'] = allStocksHist.fillna(method='ffill')
        #stock['info'] = stock['ticker'].info
    return stockList


def getInfoBuy(stockList, allStocks):
    for stock in stockList:
        stock['ticker'] = yf.Ticker(stock['stockname'])
        try:
            stock['name'] = stock['ticker'].info['shortName']
        except:
            if 'name' not in stock:
                stock['name'] = stock['stockname']
        for ourStock in allStocks:
            if stock['stockname'] in ourStock['stockname']:
                stock.update(ourStock)
    for stock in stockList:
        stock['valueNow'] = si.get_live_price(stock['stockname'])
        #stock['history'].index.get_loc(date.today(), method='nearest')
        if 'boughtValue' in stock:
            stock['boughtNetValue'] = stock['boughtValue'] + (stock['boughtFrais'] + stock['sellFrais'])/stock['boughtQ']
            stock['netActualGainPercent'] = (
                stock['valueNow'] - stock['boughtNetValue']
            ) / stock['boughtNetValue']
        if 'boughtNetValue' in stock:
            if 'sellDate' not in stock:
                stock['netActualGain'] = (stock['valueNow'] - stock['boughtNetValue']) * stock['boughtQ']
            else:
                stock['netActualGain'] = stock['sellValue'] - stock['boughtNetValue'] * stock['boughtQ']

    return stockList

def plotBasic(stock):
    fig = go.Figure(data=[
        {'y': stock['history']['Close'], 'x':stock['history'].index, 'name': 'Stock Value'},
        {'x': 
         [dfStock.index[0], dfStock.index[-1]], 
         'y': stock['boughtNetValue'] * np.ones((2)), 
         'name': 'Gain barrier'
        }
    ], layout={'title': stock['name']})
    fig.update_layout(template="plotly_dark")
    fig.show()
    
def computeIchimoku(stock):
    d = stock['history']
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
    stock['history'] = d
    return stock
    
def plotIchimoku(stock):
    d = stock['history']
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

    dataFig.append(
        {'y': custom['senkou_span_a_pos'], 'x':custom['senkou_span_a_pos'].index, 'name': 'senkou_span_a', 'opacity': 0.4, 'line': {'width':1.0, 'color': 'blue'}}
    )
    dataFig.append(
        {'y': custom['senkou_span_b_pos'], 'x':custom['senkou_span_b_pos'].index, 'name': 'senkou_span_b', 'opacity': 0.4, 'line': {'width':1.0, 'color': 'blue'}, 'fill':'tonextx'}
    )
    dataFig.append(
        {'y': custom['senkou_span_a_neg'], 'x':custom['senkou_span_a_neg'].index, 'name': 'senkou_span_a', 'opacity': 0.4, 'line': {'width':1.0, 'color': 'orange'}}
    )
    dataFig.append(
        {'y': custom['senkou_span_b_neg'], 'x':custom['senkou_span_b_neg'].index, 'name': 'senkou_span_b', 'opacity': 0.4, 'line': {'width':1.0, 'color': 'orange'}, 'fill':'tonextx'}
    )
    dataFig.append(
        {'y': custom['senkou_span_a'], 'x':custom['senkou_span_a'].index, 'name': 'senkou_span_a', 'opacity': 1.0, 'line': {'width':1.0, 'color': 'blue'}}
    )
    dataFig.append(
        {'y': custom['senkou_span_b'], 'x':custom['senkou_span_b'].index, 'name': 'senkou_span_a', 'opacity': 1.0, 'line': {'width':1.0, 'color': 'orange'}}
    )
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
    if 'boughtDate' in stock:
        dataFig.append({'x': 
            [stock['boughtDate'], stock['sellDate'] if 'sellDate' in stock else datetime.today()], 
            'y': [stock['boughtValue'], stock['boughtNetValue']], 
            'name': 'Gain barrier', 'type': 'scatter', 'mode': 'lines'
        })
        dataFig.append({
            'x': [stock['boughtDate']], 
            'y': [stock['boughtValue']], 
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
    if 'sellDate' in stock:
        dataFig.append({
            'x': [stock['sellDate']], 
            'y': [stock['sellValue']], 
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
    
    return go.Figure(data=dataFig, layout={'title': stock['name']})