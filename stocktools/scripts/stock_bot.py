import os
import json
import time
from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pandas as pd
from libsstock import (
    loadStocks, getYFdate, getInfoBuy, computeIchimoku, fillNameFromYF,
    graphIchimoku, graphBestGain, graphWorseGain, graphCashLock, graphRendement
)
from plotly_tools import genIMGfromFile
import telepot

def displayGraphValues(mybot, chat_id):
    mybot.sendMessage(
        chat_id, 'Veuillez patientez pandent la frabrication du graphe...'
    )
    df = loadStocks('mystocks.json')
    genIMGfromFile(graphRendement(df), 'img.png', scale=1.3, width=800, height=500)
    mybot.sendPhoto(chat_id, open('img.png', 'rb'))

def listMenuItems(mybot, chat_id):
    mybot.sendMessage(
        chat_id, '''
        Commandes possibles :\n
        ''' + '\n'.join(['- /' + key + ' : ' + value['details'] for key, value in availableCommands.items()])
    )

availableCommands = {
    'menu': {'fct': listMenuItems, 'details': 'Affiche les commandes disponibles.'},
    'gainetpertes': {'fct': displayGraphValues, 'details': 'Répartition des pertes et gain par actions.'},
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
        if (datetime.today().weekday() in [0, 1, 2, 3, 4] and datetime.today().hour >= 18 and datetime.today().hour <= 18):
            print('in the right timeframe, launching script')
            createMessage(mybot, bot_chatID, stockList)
        print('Sleeping 15 minutes')
        time.sleep(60 * 15)

if __name__ == '__main__':
    main()
