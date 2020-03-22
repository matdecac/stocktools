import unittest
from libsstock import (
    loadStocks, computeIchimoku, getValueDays, computeVar, checkVarPos, 
    checkVarNeg, computeVarAndStatus, genText1stock, checkVar, graphDataForStock,
    detectStockVar
)
from updateDB import (
    getStockData, getStockIntradayData,
    getLastValue, getYFdata, updateDBintradayFromSSI, updateDB
)
import pandas as pd
from datetime import date, datetime, timedelta


class TestLibsStockMethods(unittest.TestCase):
    def test_loadStocks(self):
        loadStocks('mystocks.json')
        self.assertTrue(True)
    def test_computeIchimoku(self):
        computeIchimoku(getStockData('SO.PA'))
        self.assertTrue(True)
    def test_getValueDays(self):
        getValueDays('SO.PA', getStockData('SO.PA'), 0)
        getValueDays('SO.PA', getStockData('SO.PA'), 1)
        getValueDays('SO.PA', getStockData('SO.PA'), 2)
        getValueDays('SO.PA', getStockData('SO.PA'), 3)
        self.assertTrue(True)
    def test_computeVar(self):
        computeVar(pd.Series({'stockname': 'SO.PA'}), getStockData('SO.PA'), refDay=1)
        self.assertTrue(True)
    def test_checkVarPos(self):
        checkVarPos(pd.Series({'stockname': 'SO.PA'}), getStockData('SO.PA'), refDay=1, percentVar=0.05)
        self.assertTrue(True)
    def test_checkVarNeg(self):
        checkVarNeg(pd.Series({'stockname': 'SO.PA'}), getStockData('SO.PA'), refDay=1, percentVar=-0.05)
        self.assertTrue(True)
    def test_computeVarAndStatus(self):
        computeVarAndStatus(pd.DataFrame([{'stockname': 'SO.PA'}]), getStockData('SO.PA'), refDay=1, percentVarNeg=-0.05, percentVarPos=0.05)
        self.assertTrue(True)
    def test_checkVar(self):
        checkVar(pd.DataFrame([{'stockname': 'SO.PA'}]), 5, which='all')
        self.assertTrue(True)
    def test_checkGraphDataForStock(self):
        graphDataForStock('BTC-EUR', freq=1, unit='H', histoDepth=timedelta(days=60))
        graphDataForStock('BTC-EUR', freq=5, unit='D', histoDepth=timedelta(days=60))
        self.assertTrue(True)
    def test_getStockIntradayData(self):
        getStockIntradayData('SO.PA')
        self.assertTrue(True)
    def test_getStockData(self):
        getStockData('SO.PA')
        self.assertTrue(True)
    def test_getLastValue(self):
        getLastValue('BTC-EUR')
        self.assertTrue(True)
    def test_getYFdata(self):
        getYFdata(['BTC-EUR', 'SO.PA', 'AAPL'], datetime.now() - timedelta(hours=10), interval="1m")
        getYFdata(['BTC-EUR', 'SO.PA', 'AAPL'], datetime.now() - timedelta(days=3), interval="1d")
        self.assertTrue(True)
    def test_updateDBintradayFromSSI(self):
        updateDBintradayFromSSI()
        self.assertTrue(True)
    def test_updateDB(self):
        updateDB()
        self.assertTrue(True)
    def test_detectStockVar(self):
        detectStockVar()
        self.assertTrue(True)
        
        
        
if __name__ == '__main__':
    unittest.main()