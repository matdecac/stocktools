import os
import json
import time
from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pandas as pd
from libsstock import (
    loadStocks, getYFdate, computeIchimoku, fillNameFromYF, checkVar, graphEvolutionTitre,
    graphIchimoku, graphBestGain, graphWorseGain, graphCashLock, graphRendement
)
from plotly_tools import genIMGfromFile
import telepot

def displayGraphValues(mybot, chat_id, msg):
    df = loadStocks('mystocks.json')
    genIMGfromFile(graphRendement(df), 'img.png', scale=1.3, width=800, height=500)
    mybot.sendPhoto(chat_id, open('img.png', 'rb'))

def sendVarIf(mybot, chat_id, msg):
    sendVarIfJson(mybot, chat_id, 'mystocks.json')
def sendVarIfprospects(mybot, chat_id, msg):
    sendVarIfJson(mybot, chat_id, 'stockprospects.json')

def sendVarIfJson(mybot, chat_id, fileJson):
    (strOut, dfData, historyData) = checkVar(1, fileJson)
    if len(strOut) > 0:
        mybot.sendMessage(
            chat_id, strOut
        )

def genDataFromStock(mybot, chat_id, msg):
    # recall for generate graph over a year
    #pdb.set_trace()
    stockName = msg["text"].replace('/stockinfo','').replace('_', '.')
    
    
    (strOut, dfData2, historyData) = checkVar(360, 'mystocks.json', which='all', stockName=stockName)
    listStockNames = [dfData2.loc[ind]['stockname'] for ind in dfData2.index]
    for ind in dfData2[dfData2['var1Neg']].index:
        data=genIMGfromFile(graphEvolutionTitre(historyData[ind], dfData2.iloc[ind]), 'img.png', scale=1.3, width=800, height=500)
        mybot.sendPhoto(chat_id, open('img.png', 'rb'))
        histo = computeIchimoku(historyData[ind])
        data=genIMGfromFile(graphIchimoku(
            dfData2[dfData2['stockname'] == listStockNames[ind]], histo
        ), 'img.png', scale=1.3, width=800, height=500)
        mybot.sendPhoto(chat_id, open('img.png', 'rb'))
    for ind in dfData2[dfData2['var1Pos']].index:
        data=genIMGfromFile(graphEvolutionTitre(historyData[ind], dfData2.iloc[ind]), 'img.png', scale=1.3, width=800, height=500)
        mybot.sendPhoto(chat_id, open('img.png', 'rb'))
        histo = computeIchimoku(historyData[ind])
        data=genIMGfromFile(graphIchimoku(
            dfData2[dfData2['stockname'] == listStockNames[ind]], histo
        ), 'img.png', scale=1.3, width=800, height=500)
        mybot.sendPhoto(chat_id, open('img.png', 'rb'))

def listMenuItems(mybot, chat_id, msg):
    mybot.sendMessage(
        chat_id, '''
        Commandes possibles :\n
        ''' + '\n'.join(['- /' + key + ' : ' + value['details'] for key, value in availableCommands.items()])
    )

availableCommands = {
    'menu': {'fct': listMenuItems, 'details': 'Affiche les commandes disponibles.'},
    'gainetpertes': {'fct': displayGraphValues, 'details': 'Répartition des pertes et gain par actions.'},
    'varportefeuille': {'fct': sendVarIf, 'details': 'Visualiser les variations sur les valeurs.'},
    'varprospects': {'fct': sendVarIfprospects, 'details': 'Visualiser les variations sur les valeurs en prospects.'},
    'stockinfo': {'fct': genDataFromStock, 'details': 'Visualiser les variations sur les valeurs en prospects.'},
}

def handle(msg):
    global mybot
    content_type, chat_type, chat_id = telepot.glance(msg)
    msgDecoded = False
    
    if content_type == 'text':
        for cmd, value in availableCommands.items():
            if '/' + cmd in msg["text"]:
                msgDecoded = True
                value['fct'](mybot, chat_id, msg)
    if not msgDecoded:
        mybot.sendMessage(chat_id, "Message '{}' non géré, essayez /menu.".format(msg["text"]))



def main():
    global mybot
    bot_token = '***REMOVED***'
    bot_chatID = '***REMOVED***'
    mybot = telepot.Bot(bot_token)
    mybot.message_loop(handle)
    mybot.sendMessage(
        bot_chatID, '''
        Bonjour, bienvenue sur le bot financier, essayer /menu pour les fonctions.
        '''
    )
    while(1):
        thisHourSend = datetime.today().hour
        if (datetime.today().weekday() in [0, 1, 2, 3, 4] and datetime.today().hour + 2 >= 9 and datetime.today().hour + 2 <= 18):
            sendVarIf(mybot, bot_chatID)
            sendVarIfprospects(mybot, bot_chatID)
        print('Sleeping 15 minutes')
        time.sleep(60 * 15)

if __name__ == '__main__':
    main()


