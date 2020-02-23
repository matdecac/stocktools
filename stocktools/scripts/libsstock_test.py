import unittest
from libsstock import loadStocks, computeIchimoku, getValueDays, computeVar, checkVarPos, checkVarNeg, computeVarAndStatus, genText1stock, checkVar, graphDataForStock
from updateDB import getStockData
import pandas as pd
from datetime import timedelta

class TestLibsStockMethods(unittest.TestCase):
    def test_loadStocks(self):
        loadStocks('mystocks.json')
        self.assertTrue(True)
    def test_computeIchimoku(self):
        computeIchimoku(getStockData('SO.PA'))
        self.assertTrue(True)
    def test_getValueDays(self):
        getValueDays(getStockData('SO.PA'), 0)
        getValueDays(getStockData('SO.PA'), 1)
        getValueDays(getStockData('SO.PA'), 2)
        getValueDays(getStockData('SO.PA'), 3)
        self.assertTrue(True)
    def test_computeVar(self):
        computeVar(pd.DataFrame([{'stockname': 'SO.PA'}]), getStockData('SO.PA'), refDay=1)
        self.assertTrue(True)
    def test_checkVarPos(self):
        checkVarPos(pd.DataFrame([{'stockname': 'SO.PA'}]), getStockData('SO.PA'), refDay=1, percentVar=0.05)
        self.assertTrue(True)
    def test_checkVarNeg(self):
        checkVarNeg(pd.DataFrame([{'stockname': 'SO.PA'}]), getStockData('SO.PA'), refDay=1, percentVar=-0.05)
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

if __name__ == '__main__':
    unittest.main()