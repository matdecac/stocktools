from libsstock import getInfoBuy, getYFdate, computeIchimoku, plotIchimoku
from stockList import stockList
import telepot
import time
from datetime import datetime, date, timedelta
from plotly_tools import genIMGfromFile



def createMessage(mybot, chatid, stockList, diffLimit=0.0):
    stockProspect = getInfoBuy(stockList, stockList)
    strOut = ''
    for stock in stockProspect:
        diff = stock['valueNow'] - stock['boughtNetValue']
        if diff*stock['boughtQ'] > diffLimit:
            strOut += stock['name'] + ' :\n'
            strOut += ' - boughtNetValue : {:.3f} €\n'.format(stock['boughtNetValue'])
            strOut += ' - valueNow       : {:.3f} €\n'.format(stock['valueNow'])
            strOut += ' - diff           : {:.3f} €\n'.format(diff)
            strOut += ' - cashIn         : {:.2f} €\n'.format(diff*stock['boughtQ']) 
            #plotBasic(stock)
            stockOut = getYFdate(
                [stock], 
                startDate=date.today() - timedelta(days=41+3*31), 
                stopDate=date.today() + timedelta(days=1)
            )
            stock = computeIchimoku(stockOut[0])
            fig = plotIchimoku(stock)
            fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=600)
            #fig.show() # while plotly is not working with jupyter lab
            dataImg = genIMGfromFile(fig, 'img.png', scale=1.3)
            #display(ImageD(data=dataImg))
            mybot.sendPhoto(chatid, open('img.png', 'rb'))
    mybot.sendMessage(chatid, strOut)


def main():
    bot_token = '***REMOVED***'
    bot_chatID = '***REMOVED***'
    mybot = telepot.Bot(bot_token)
    while(1):
        lastHourSend = -1
        thisHourSend = datetime.today().hour
        if datetime.today().weekday() in [0, 1, 2, 3, 4] and datetime.today().hour >= 9 and datetime.today().hour <= 21:
            print('in the right timeframe, launching script')
            diffDec = 0.0
            if thisHourSend > lastHourSend:
                lastHourSend = thisHourSend
                diffDec = -10000
            createMessage(mybot, bot_chatID, stockList, diffLimit=diffDec)
        print('Sleeping 15 minutes')
        time.sleep(60 * 15)
if __name__ == '__main__':
    main()