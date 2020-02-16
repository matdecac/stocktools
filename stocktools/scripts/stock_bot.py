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

def displayGraphValues(mybot, chat_id):
    mybot.sendMessage(
        chat_id, 'Veuillez patientez pendant la frabrication du graphe...'
    )
    df = loadStocks('mystocks.json')
    genIMGfromFile(graphRendement(df), 'img.png', scale=1.3, width=800, height=500)
    mybot.sendPhoto(chat_id, open('img.png', 'rb'))

def sendVarIf(mybot, chat_id):
    sendVarIfJson(mybot, chat_id, 'mystocks.json')
def sendVarIfprospects(mybot, chat_id):
    sendVarIfJson(mybot, chat_id, 'stockprospects.json')

def sendVarIfJson(mybot, chat_id, fileJson):
    mybot.sendMessage(
        chat_id, 'Veuillez patientez pendant la recherche de données...'
    )
    (strOut, dfData, historyData) = checkVar(1, fileJson)
    if len(strOut) > 0:
        mybot.sendMessage(
            chat_id, strOut
        )
        # recall for generate graph over a year
        (strOut, dfData2, historyData) = checkVar(360, fileJson)
        listStockNames = [dfData2.loc[ind]['stockname'] for ind in dfData2.index]
        for ind in dfData[dfData['var1Neg']].index:
            data=genIMGfromFile(graphEvolutionTitre(historyData[ind], dfData.iloc[ind]), 'img.png', scale=1.3, width=800, height=500)
            mybot.sendPhoto(chat_id, open('img.png', 'rb'))
            histo = computeIchimoku(historyData[ind])
            data=genIMGfromFile(graphIchimoku(
                dfData[dfData['stockname'] == listStockNames[ind]], histo
            ), 'img.png', scale=1.3, width=800, height=500)
            mybot.sendPhoto(chat_id, open('img.png', 'rb'))
        for ind in dfData[dfData['var1Pos']].index:
            data=genIMGfromFile(graphEvolutionTitre(historyData[ind], dfData.iloc[ind]), 'img.png', scale=1.3, width=800, height=500)
            mybot.sendPhoto(chat_id, open('img.png', 'rb'))
            histo = computeIchimoku(historyData[ind])
            data=genIMGfromFile(graphIchimoku(
                dfData[dfData['stockname'] == listStockNames[ind]], histo
            ), 'img.png', scale=1.3, width=800, height=500)
            mybot.sendPhoto(chat_id, open('img.png', 'rb'))
    else:
        mybot.sendMessage(
            chat_id, 'Pas de variations'
        )

def listMenuItems(mybot, chat_id):
    mybot.sendMessage(
        chat_id, '''
        Commandes possibles :\n
        ''' + '\n'.join(['- /' + key + ' : ' + value['details'] for key, value in availableCommands.items()])
    )

availableCommands = {
    'menu': {'fct': listMenuItems, 'details': 'Affiche les commandes disponibles.'},
    'gainetpertes': {'fct': displayGraphValues, 'details': 'Répartition des pertes et gain par actions.'},
    'variations': {'fct': sendVarIf, 'details': 'Visualiser les variations sur les valeurs.'},
    'variationsprospects': {'fct': sendVarIfprospects, 'details': 'Visualiser les variations sur les valeurs en prospects.'},
}

def handle(msg):
    global mybot
    content_type, chat_type, chat_id = telepot.glance(msg)
    
    if content_type == 'text':
        if msg["text"] in ['/' + value for value in availableCommands.keys()]:
            for cmd, value in availableCommands.items():
                if msg["text"] == '/' + cmd:
                    value['fct'](mybot, chat_id)
        else:
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
        if (datetime.today().weekday() in [0, 1, 2, 3, 4] and datetime.today().hour >= 9 and datetime.today().hour <= 18):
            sendVarIf(mybot, bot_chatID)
            sendVarIfprospects(mybot, bot_chatID)
        print('Sleeping 15 minutes')
        time.sleep(60 * 15)

if __name__ == '__main__':
    main()


