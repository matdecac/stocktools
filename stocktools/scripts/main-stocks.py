#!/Users/matdecac/Documents/repositories/compta/venv/bin/python3
# -*- coding: utf-8 -*-
#
# main.py
# Dash library tests
#
# Created by Mathias de Cacqueray on 16/10/2018.
#
# Copyright (c) 2018 Mathias de Cacqueray. All rights reserved.
# Repository created by Mathias de Cacqueray, You should read LICENSE.

import os
import locale

#locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
#locale.setlocale(locale.LC_NUMERIC, 'en_US.UTF-8')
import json
from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from libsstock import (
    loadStocks, getYFdate, getInfoBuy, computeIchimoku, fillNameFromYF,
    graphIchimoku
)

jsonToUpdate = 'stockprospects.json'
df = pd.read_json(jsonToUpdate, orient='index')

app = dash.Dash(external_stylesheets=[dbc.themes.CYBORG])
server = app.server

debugMode = True


app.layout = dbc.Container(fluid=True, children=[
    dbc.Row([
        dbc.Col([
            dcc.Markdown(
                id='main-text-header',
                children='# Compta decac',
                className="dash-bootstrap"
            ),
        ], md=2, xs=12),
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    dcc.Dropdown(
                        id='list-stock',
                        options=[{'label':df.loc[ind]['name'], 'value':df.loc[ind]['stockname']} for ind in df.index],
                        value=[],
                        placeholder="Choisir Stock",
                        multi=False,
                    ),
                ], md=3, xs=12),
                dbc.Col([
                    dbc.Input(
                        id='text-plot-stock',
                        placeholder='Enter a stock',
                        type='text',
                        value=''
                    )
                ], md=3, xs=12),
                dbc.Col([
                    dcc.DatePickerSingle(
                        id='choose-date-start',
                        date=date.today() - timedelta(days=365+41),
                        display_format='D/M/Y',
                        month_format='D/M/Y',
                        placeholder='D/M/Y',
                        className="dash-bootstrap",
                    ),
                ], md=2, xs=12),
                dbc.Col([
                    dcc.DatePickerSingle(
                        id='choose-date-stop',
                        date=date.today() + timedelta(days=1),
                        display_format='D/M/Y',
                        month_format='D/M/Y',
                        placeholder='D/M/Y',
                        className="dash-bootstrap",
                    ),
                ], md=2, xs=12),
            ], align="center", justify="center"),
        ], md=10, xs=12),
    ]),
    dcc.Graph(
        id='graph-stock',
        figure={
            'data': [],
            'layout': dict(template="plotly_dark")
        },
        style={'height': 1000},
    ),
    dcc.Store(id='page-full-state', storage_type='memory', data={}),
    html.Link(rel='stylesheet',href='/assets/bootstrap-4.3.1-dist/css/bootstrap.min.css'),
    html.Link(rel='stylesheet',href='/assets/bootstrap-4.3.1-dist/css/bootstrap.min.css.map'),
    html.Link(rel='stylesheet',href='/assets/bootstrap-4.3.1-dist/js/bootstrap.bundle.min.js'),
    html.Link(rel='stylesheet',href='/assets/bootstrap-4.3.1-dist/js/bootstrap.bundle.min.js.map'),
    html.Link(rel='stylesheet',href='/assets/bootstrap-4.3.1-dist/js/bootstrap.min.js'),
    html.Link(rel='stylesheet',href='/assets/bootstrap-4.3.1-dist/js/bootstrap.min.js.map'),
])



@app.callback(
    [
        Output("text-plot-stock", "value")
    ],
    [
        Input("list-stock", "value"),
    ],
)
def update_options(value):
    if len(value) > 0:
        value = value
    else:
        value = ''
    return [value]

@app.callback(
    [
        Output("graph-stock", "figure")
    ],
    [
        Input("text-plot-stock", "value"),
        Input('choose-date-start', 'date'),
        Input('choose-date-stop', 'date'),
    ],
)
def update_options(value, dateStart, dateStop):
    print(len(value))
    if len(value) >= 0:
        try:
            df = pd.DataFrame([{'stockname': value}])
            dfData = loadStocks('mystocks.json')
            dfData = dfData[dfData['stockname'] == df.iloc[0]['stockname']]
            if len(dfData) > 0:
                df = dfData
            else:
                df = fillNameFromYF(df)
            dfHist = getYFdate(df, dateStart, dateStop)
            dfHist = computeIchimoku(dfHist[0])
            return [graphIchimoku(df, dfHist).update({'layout': dict(template="plotly_dark", xaxis_rangeslider_visible=False)})]
        except:
            raise PreventUpdate
    else:
        raise PreventUpdate 


app.css.config.serve_locally = True
app.scripts.config.serve_locally = True

# serve files in static (mainly maps tiles)
app.server.static_folder = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'static'
)

@app.server.route('/assets/<path:path>')
def static_file(path):
    static_folder = os.path.join(os.getcwd(), 'assets')
    return send_from_directory(static_folder, path)


if __name__ == '__main__':
    app.run_server(debug=debugMode, host='0.0.0.0')
