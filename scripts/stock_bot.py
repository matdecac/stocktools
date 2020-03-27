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
    graphEvolutionIntraday, graphDataForStock, detectStockVar, computeParms,
    computeRRvals
)
from plotly_tools import genIMGfromFile
import telepot
from updateDB import (
    updateDB, getStockData, updateDBintradayFromSSI,
    addBoughtLine, addSoldLine, isMarketOpen
)

def genBoughtLine(mybot, chat_id, msg):
    strOut = addBoughtLine(msg['text'])
    strOut += computeRRvalues(msg['text'])
    mybot.sendMessage(
        chat_id, strOut
    )
def genSoldLine(mybot, chat_id, msg):
    strOut = addSoldLine(msg['text'])
    mybot.sendMessage(
        chat_id, strOut
    )

def computeBuyParms(mybot, chat_id, msg):
    msgText = msg['text'].split(' ')
    (boughtQ, investCash, valBuy) = computeParms(float(msgText[1]), float(msgText[2]))
    rrVals = computeRRvals(valBuy, float(msgText[1]), maxLoss=0.05, riskRewardRatio=2)
    strOut = 'Ordre à seuil de déclenchement :\n'
    strOut += '- Q={:.0f}, PRU={:.3f} €, capital={:.3f} €, Frais: {:.1f}\n'.format(boughtQ, valBuy, investCash, rrVals['impactFrais'] * 100)
    strOut += '- Stoploss: {:.2f} € / {:.1f} %\n'.format(rrVals['stopLossVal'], rrVals['stopLossRatio'] * 100)
    strOut += '- Sell    : {:.2f} € / {:.1f} %\n'.format(rrVals['takeProfitVal'], rrVals['takeProfitRatio'] * 100)
    mybot.sendMessage(
        chat_id, strOut
    )
    
def loopUpdateDB(mybot, bot_chatID):
    while(1):
        try:
            updateDB(daysHisto=1, stockRes='daily')
            updateDB(daysHisto=1, stockRes='intraday')
            logging.info('Sleeping 30 minutes')
        except Exception as e: 
            print(e)
            logging.error('loopUpdateDB')
            logging.error(e)
            mybot.sendMessage(chat_id, "Error : \n" + str(e))
        time.sleep(60 * 30)

def loopUpdateDBintraday(mybot, bot_chatID):
    while(1):
        try:
            if isMarketOpen(market='PA'):
                updateDBintradayFromSSI()
                (strOut, listStocks) = detectStockVar(datetime.now() - timedelta(minutes=120))
                if len(strOut) > 0:
                    mybot.sendMessage(
                        bot_chatID, strOut
                    ) 
            logging.info('Sleeping 0.5 minutes')
        except Exception as e:
            logging.error('loopUpdateDBintraday')
            logging.error(e)
            mybot.sendMessage(bot_chatID, "Error : \n" + str(e))
        time.sleep(60 * 0.5)

def displayGraphValues(mybot, chat_id, msg):
    df = loadStocks('mystocks.json')
    dfS = df[df['sellValue'].isna()].sort_values('boughtDate')
    strOut = ''
    for lineIND in dfS.index:
        line = dfS.loc[lineIND]
        strOut += line['name'] + " / " + line['stockname'] + " / " + "/stockinfo" + str(line['stockname']).replace('.', '_') + '\n'

        strOut += "- PRU      : {:.2f} €\n".format(line['boughtNetValue'])
        strOut += "- COURS    : {:.2f} €\n".format(line['valueNow'])
        strOut += "- CAPITAL  : {:.2f} €\n".format(line['netActualLock'])
        strOut += "- LOSS/GAIN: {:.2f} % / {:.2f} €\n".format(line['netActualGainPercent'], line['netActualGain'])
    mybot.sendMessage(chat_id, strOut)

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
    #graphDataA.append(graphEvolutionTitre(stockName))
    #graphDataA.append(graphDataForStock(stockName, freq=1, unit='W', histoDepth=timedelta(days=360)))
    #graphDataA.append(graphDataForStock(stockName, freq=1, unit='D', histoDepth=timedelta(days=60)))
    graphDataA.append(graphDataForStock(stockName, freq=5, unit='T', histoDepth=timedelta(days=0)))
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
    'buy': {'fct': genBoughtLine, 'details': 'Ajouter un achat : /buy NOM VALEURUNIT Q.'},
    'sell': {'fct': genSoldLine, 'details': 'Ajouter une vente : /sell NOM VALEURUNIT.'},
    'computeparmsbuy': {'fct': computeBuyParms, 'details': 'Paramètres d\'achats /computeparmsbuy valeur_unitaire budget_invest'},
    
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
    with open('credential.secret', 'r') as infile:
        creds = json.load(infile)
    bot_token = creds['bot_token']
    bot_chatID = creds['bot_chatID']
    alphaVantage= creds['av_token']
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


    dbUpdate = threading.Thread(name='dbupdate', target=loopUpdateDB, daemon=True, args=[mybot, bot_chatID])
    dbUpdateIntraday = threading.Thread(name='dbupdateintraday', target=loopUpdateDBintraday, daemon=True, args=[mybot, bot_chatID])
    dbUpdate.start()
    dbUpdateIntraday.start()

    while(1):
        print('Sleeping 60 minutes')
        time.sleep(60 * 60)

if __name__ == '__main__':
    main()






