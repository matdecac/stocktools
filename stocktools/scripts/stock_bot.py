import os
import json
import threading
import time
import logging
from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pandas as pd
from libsstock import (
    loadStocks, computeIchimoku, checkVar, graphEvolutionTitre,
    graphIchimoku, graphBestGain, graphWorseGain, graphCashLock, graphRendement,
    graphEvolutionIntraday, graphDataForStock
)
from plotly_tools import genIMGfromFile
import telepot
from updateDB import updateDB, getStockData, updateDBintraday

def loopUpdateDB():
    while(1):
        #if (datetime.today().weekday() in [0, 1, 2, 3, 4] and datetime.today().hour + 2 >= 9 and datetime.today().hour + 2 <= 18):
        updateDB()
        logging.info('Sleeping 5 minutes')
        time.sleep(60 * 5)
def loopUpdateDBintraday():
    while(1):
        #if (datetime.today().weekday() in [0, 1, 2, 3, 4] and datetime.today().hour + 2 >= 9 and datetime.today().hour + 2 <= 18):
        updateDBintraday()
        logging.info('Sleeping 0.5 minutes')
        time.sleep(60 * 0.5)

def displayGraphValues(mybot, chat_id, msg):
    df = loadStocks('mystocks.json')
    genIMGfromFile(graphRendement(df), 'img.png', scale=1.3, width=800, height=500)
    mybot.sendPhoto(chat_id, open('img.png', 'rb'))

def sendVarIf(mybot, chat_id, msg):
    sendVarIfJson(mybot, chat_id, 'mystocks.json')
def sendVarIfALL(mybot, chat_id, msg):
    sendVarIfJsonALL(mybot, chat_id, 'mystocks.json')
def sendVarIfprospects(mybot, chat_id, msg):
    sendVarIfJson(mybot, chat_id, 'stockprospects.json')

def sendVarIfprospectsALL(mybot, chat_id, msg):
    sendVarIfJsonALL(mybot, chat_id, 'stockprospects.json')


def sendVarIfJson(mybot, chat_id, fileJson):
    df = loadStocks(fileJson)
    if "netActualGain" in df.columns:
        df = df[df['sellDate'].isna()]
    else:
        df = df.drop_duplicates(subset='stockname')
    (strOut, dfData) = checkVar(df, 1, which='pos')
    df = loadStocks(fileJson)
    if "netActualGain" in df.columns:
        df = df[df['sellDate'].isna()]
    else:
        df = df.drop_duplicates(subset='stockname')
    (strOut2, dfData) = checkVar(df, 1, which='neg')
    if len(strOut + strOut2) > 0:
        mybot.sendMessage(
            chat_id, strOut + strOut2
        )

        
def sendVarIfJsonALL(mybot, chat_id, fileJson):
    df = loadStocks(fileJson)
    if "netActualGain" in df.columns:
        df = df[df['sellDate'].isna()]
    else:
        df = df.drop_duplicates(subset='stockname')
    (strOut, dfData) = checkVar(df, 1, which='all')
    if len(strOut) > 0:
        mybot.sendMessage(
            chat_id, strOut
        )

def genDataFromStock(mybot, chat_id, msg):
    # recall for generate graph over a year
    #pdb.set_trace()
    stockName = msg["text"].replace('/stockinfo','').replace('_', '.')
    print('Generate data for ' + stockName)
    mybot.sendMessage(
        chat_id, 'Generate data for ' + stockName
    )
    graphDataA = []
    graphDataA.append(graphEvolutionTitre(stockName))
    graphDataA.append(graphDataForStock(stockName, freq=1, unit='W', histoDepth=timedelta(days=360)))
    graphDataA.append(graphDataForStock(stockName, freq=1, unit='D', histoDepth=timedelta(days=60)))
    graphDataA.append(graphDataForStock(stockName, freq=5, unit='T', histoDepth=timedelta(days=1)))
    for graphData in graphDataA:
        if graphData is not None:
            genIMGfromFile(graphData, 'img.png', scale=1.3, width=800, height=500)
            mybot.sendPhoto(chat_id, open('img.png', 'rb'))
        else:
            mybot.sendMessage(chat_id, 'Certains graphes n\'ont pas pu être généré')
    

def listMenuItems(mybot, chat_id, msg):
    mybot.sendMessage(
        chat_id, '''
        Commandes possibles :\n
        ''' + '\n'.join(['- /' + key + ' : ' + value['details'] for key, value in availableCommands.items()])
    )

availableCommands = {
    'menu': {'fct': listMenuItems, 'details': 'Affiche les commandes disponibles.'},
    'gainetpertes': {'fct': displayGraphValues, 'details': 'Répartition des pertes et gain par actions.'},
    'varportefeuille': {'fct': sendVarIfALL, 'details': 'Visualiser les variations sur les valeurs.'},
    'varprospects': {'fct': sendVarIfprospectsALL, 'details': 'Visualiser les variations sur les valeurs en prospects.'},
    'stockinfo': {'fct': genDataFromStock, 'details': 'Visualiser les variations sur les valeurs en prospects.'},
}

def handle(msg):
    try:
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
    except Exception as e: 
        print(e)
        mybot.sendMessage(chat_id, "Error : \n" + str(e))


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
    logging.basicConfig(
        level=logging.DEBUG,
        format='(%(threadName)-10s) %(message)s',
    )


    dbUpdate = threading.Thread(name='dbupdate', target=loopUpdateDB, daemon=True)
    dbUpdateIntraday = threading.Thread(name='dbupdateintraday', target=loopUpdateDBintraday, daemon=True)
    dbUpdate.start()
    dbUpdateIntraday.start()

    while(1):
        try:
            thisHourSend = datetime.today().hour
            if (datetime.today().weekday() in [0, 1, 2, 3, 4] and datetime.today().hour + 2 >= 9 and datetime.today().hour + 2 <= 18):
                sendVarIf(mybot, bot_chatID, None)
                #sendVarIfprospects(mybot, bot_chatID, None)
        except:
            pass
        print('Sleeping 5 minutes')
        time.sleep(60 * 5)

if __name__ == '__main__':
    main()






