from libsstock import getInfoBuy
from stockList import stockList
import requests


def telegram_bot_sendtext(bot_message):
    
    bot_token = '***REMOVED***'
    bot_chatID = '***REMOVED***'
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message

    response = requests.get(send_text)

    return response.json()



def createMessage(stockList):
    stockProspect = getInfoBuy(stockList, stockList)
    for stock in stockProspect:
        diff = stock['valueNow'] - stock['boughtNetValue']
        if diff > -10000:
            strOut = stock['name'] + ' :\n'
            strOut += ' - boughtNetValue : {:.3f} €\n'.format(stock['boughtNetValue'])
            strOut += ' - valueNow       : {:.3f} €\n'.format(stock['valueNow'])
            strOut += ' - diff           : {:.3f} €\n'.format(diff)
            strOut += ' - cashIn         : {:.2f} €\n'.format(diff*stock['boughtQ']) 
            telegram_bot_sendtext(strOut)



createMessage(stockList)
