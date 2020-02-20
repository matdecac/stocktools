#!/bin/python
# manage.sh
# SQL docker launcher
#
# Created by Mathias de Cacqueray Valmenier on 23/06/2018.
# Copyright (c) 2018 Mathias de Cacqueray Valmenier. All rights reserved.
# Repository created by Mathias de Cacqueray, You should read LICENSE.


from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class StockDay(Base):
    __tablename__ = 'stockday'
    id = Column(Integer, primary_key=True)
    stockname = Column(String, nullable=False)
    datestamp = Column(Date, nullable=False)
    priceOpen = Column(Float)
    priceHigh = Column(Float)
    priceLow = Column(Float)
    priceClose = Column(Float)
    priceAdjClose = Column(Float)
    volume = Column(Integer)
    dateadded = Column(DateTime)
class StockIntraDay(Base):
    __tablename__ = 'stockintraday'
    id = Column(Integer, primary_key=True)
    stockname = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    dateadded = Column(DateTime)
    price = Column(Float)