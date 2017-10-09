# encoding: UTF-8

from vnpy.trader.app.spreadTrading.stEngine import StEngine
from vnpy.trader.app.spreadTrading.uiStWidget import StManager

appName = 'SpreadTrading'
appDisplayName = u'价差交易'
appEngine = StEngine
appWidget = StManager
appIco = 'st.ico'