# encoding: UTF-8

from __future__ import division

from datetime import datetime
from math import floor

import pandas as pd
import numpy as np

import sys
sys.path.append('../')
#sys.path.append('D:\\tr\\vnpy-master\\vn.trader\\DAO')
sys.path.append('D:\\tr\\vnpy-1.7\\vnpy\\DAO')
sys.path.append('D:\\tr\\vnpy-1.7\\vnpy\\common')
import vnpy.DAO
import vnpy.common
from vnpy.DAO import *

from vnpy.trader.vtConstant import (EMPTY_INT, EMPTY_FLOAT,
                                    EMPTY_STRING, EMPTY_UNICODE)



EVENT_SPREADTRADING_TICK = 'eSpreadTradingTick.'
EVENT_SPREADTRADING_POS = 'eSpreadTradingPos.'
EVENT_SPREADTRADING_LOG = 'eSpreadTradingLog'
EVENT_SPREADTRADING_ALGO = 'eSpreadTradingAlgo.'
EVENT_SPREADTRADING_ALGOLOG = 'eSpreadTradingAlgoLog'



########################################################################
class StLeg(object):
    """"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.vtSymbol = EMPTY_STRING      # 代码
        self.ratio = EMPTY_INT          # 实际交易时的比例
        self.multiplier = EMPTY_FLOAT   # 计算价差时的乘数
        self.payup = EMPTY_INT          # 对冲时的超价tick
        
        self.bidPrice = EMPTY_FLOAT
        self.askPrice = EMPTY_FLOAT
        self.bidVolume = EMPTY_INT
        self.askVolume = EMPTY_INT
        
        self.longPos = EMPTY_INT
        self.shortPos = EMPTY_INT
        self.netPos = EMPTY_INT

        self.actleg = EMPTY_INT
        self.actlegPos = EMPTY_FLOAT
        self.passleg = EMPTY_INT
        self.passlegPos = EMPTY_FLOAT
        self.profitloss = EMPTY_FLOAT

########################################################################
class StSpread(object):
    """"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.name = EMPTY_UNICODE       # 名称
        self.symbol = EMPTY_STRING      # 代码（基于组成腿计算）
        
        self.activeLeg = None           # 主动腿
        self.passiveLegs = []           # 被动腿（支持多条）
        self.allLegs = []               # 所有腿
        
        self.bidPrice = EMPTY_FLOAT
        self.askPrice = EMPTY_FLOAT
        self.bidVolume = EMPTY_INT
        self.askVolume = EMPTY_INT
        self.time = EMPTY_STRING
        
        self.longPos = EMPTY_INT
        self.shortPos = EMPTY_INT
        self.netPos = EMPTY_INT

        self.actlegLongPos = EMPTY_INT
        self.actlegLongValue = EMPTY_FLOAT
        self.actlegShortPos = EMPTY_INT
        self.actlegShortValue = EMPTY_FLOAT

        self.passlegLongPos = EMPTY_INT
        self.passlegLongValue = EMPTY_FLOAT
        self.passlegShortgPos = EMPTY_INT
        self.passlegShortValue = EMPTY_FLOAT

        self.profitloss = EMPTY_FLOAT

    #----------------------------------------------------------------------
    def initSpread(self):
        """初始化价差"""
        # 价差最少要有一条主动腿
        if not self.activeLeg:
            return
        
        # 生成所有腿列表
        self.allLegs.append(self.activeLeg)
        self.allLegs.extend(self.passiveLegs)
        
        # 生成价差代码
        legSymbolList = []
        
        for leg in self.allLegs:
            if leg.multiplier >= 0:
                legSymbol = '+%s*%s' %(leg.multiplier, leg.vtSymbol)
            else:
                legSymbol = '%s*%s' %(leg.multiplier, leg.vtSymbol)
            legSymbolList.append(legSymbol)
        
        self.symbol = ''.join(legSymbolList)
        
    #----------------------------------------------------------------------
    def calculatePrice(self):
        """计算价格"""
        # 清空价格和委托量数据
        self.bidPrice = EMPTY_FLOAT
        self.askPrice = EMPTY_FLOAT
        self.askVolume = EMPTY_INT
        self.bidVolume = EMPTY_INT
        
        # 遍历价差腿列表
        for n, leg in enumerate(self.allLegs):
            # 计算价格
            if leg.multiplier > 0:
                self.bidPrice += leg.bidPrice * leg.multiplier
                self.askPrice += leg.askPrice * leg.multiplier
            else:
                self.bidPrice += leg.askPrice * leg.multiplier
                self.askPrice += leg.bidPrice * leg.multiplier
                
            # 计算报单量:floor向下取整
            if leg.ratio > 0:
                legAdjustedBidVolume = floor(leg.bidVolume / leg.ratio)
                legAdjustedAskVolume = floor(leg.askVolume / leg.ratio)
            else:
                legAdjustedBidVolume = floor(leg.askVolume / abs(leg.ratio))
                legAdjustedAskVolume = floor(leg.bidVolume / abs(leg.ratio))
            
            if n == 0:
                self.bidVolume = legAdjustedBidVolume                           # 对于第一条腿，直接初始化
                self.askVolume = legAdjustedAskVolume
            else:
                self.bidVolume = min(self.bidVolume, legAdjustedBidVolume)      # 对于后续的腿，价差可交易报单量取较小值
                self.askVolume = min(self.askVolume, legAdjustedAskVolume)
                
        # 更新时间
        self.time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        
    #----------------------------------------------------------------------
    def calculatePos(self):
        """计算持仓"""
        # 清空持仓数据
        self.longPos = EMPTY_INT
        self.shortPos = EMPTY_INT
        self.netPos = EMPTY_INT

        self.actlegLongPos = EMPTY_INT
        self.actlegLongValue = EMPTY_FLOAT
        self.actlegShortPos = EMPTY_INT
        self.actlegShortValue = EMPTY_FLOAT

        self.passlegLongPos = EMPTY_INT
        self.passlegLongValue = EMPTY_FLOAT
        self.passlegShortgPos = EMPTY_INT
        self.passlegShortValue = EMPTY_FLOAT

        self.profitloss = EMPTY_FLOAT
        
        # 遍历价差腿列表
        for n, leg in enumerate(self.allLegs):
            if leg.ratio > 0:
                legAdjustedLongPos = floor(leg.longPos / leg.ratio)
                legAdjustedShortPos = floor(leg.shortPos / leg.ratio)
            else:
                legAdjustedLongPos = floor(leg.shortPos / abs(leg.ratio))
                legAdjustedShortPos = floor(leg.longPos / abs(leg.ratio))

            if n == 0:
                self.longPos = legAdjustedLongPos
                self.shortPos = legAdjustedShortPos
            else:
                self.longPos = min(self.longPos, legAdjustedLongPos)
                self.shortPos = min(self.shortPos, legAdjustedShortPos)

            #计算浮动盈亏
            sql = ' SELECT LONG_POSITION, LONG_POSITION*LONG_OPEN_AVG_PRICE,SHORT_POSITION,SHORT_POSITION*SHORT_OPEN_AVG_PRICE' \
                  ' from defer_real_hold where SYMBOL = \'%s\' and STRATAGE = \'%s\' ' % (leg.vtSymbol, self.name)
            #retPos = vnpy.DAO.getDataBySQL('vnpy', sql)
            print (u'leginfo:vtSymbol=%s,name=%s' % (leg.vtSymbol, self.name))
            retPos = vnpy.DAO.getDataBySQL('vnpy', sql)
            # 根据以上条件查询出的默认持仓只有一条记录,目前被动腿也只有一条leg
            print retPos
            print leg
            print self.activeLeg,self.passiveLegs
            if leg == self.activeLeg:
                print (u'leginfo:self.askPrice=%s' % (str(self.askPrice)))
                self.actlegLongPos = retPos.icol(0).get_values()
                self.actlegLongValue = retPos.icol(1).get_values()
                self.actlegShortPos = retPos.icol(2).get_values()
                self.actlegShortValue = retPos.icol(3).get_values()
                print self.actlegLongPos,self.actlegLongValue,self.actlegShortPos,self.actlegShortValue
            #被动腿有可能有多条腿
            elif leg in self.passiveLegs:
                self.passlegLongPos += retPos.icol(0).get_values()
                self.passlegLongValue += retPos.icol(1).get_values()
                self.passlegShortgPos += retPos.icol(2).get_values()
                self.passlegShortValue += retPos.icol(3).get_values()
            else:
                pass

            #浮动盈亏=主动腿盈亏+被动腿盈亏
            self.profitloss = (self.actlegLongValue - self.actlegLongPos * leg.askPrice ) + (self.passlegShortValue - self.passlegShortgPos * leg.bidPrice) \
                       + (self.actlegShortValue - self.actlegShortPos * leg.bidPrice) + ( self.passlegLongValue - self.passlegLongPos * leg.askPrice)
            #self.profitloss = self.actlegLongPos*self.askPrice + self.actlegShortPos*self.bidPrice

            print (u'leginfo:self.actleg=%s,self.actlegPos=%s,self.profitloss=%s' % (str(self.actlegLongPos), str(self.actlegLongValue),str(self.profitloss)))

        # 计算净仓位
        self.longPos = int(self.longPos)
        self.shortPos = int(self.shortPos)
        self.netPos = self.longPos - self.shortPos

        #wzhua 20170917 新增计算浮动盈亏
        self.actlegLongPos = int(self.actlegLongPos)
        self.actlegLongValue = float(self.actlegLongValue)
        self.actlegShortPos = int(self.actlegShortPos)
        self.actlegShortValue = float(self.actlegShortValue)

        self.passlegLongPos = int(self.passlegLongPos)
        self.passlegLongValue = float(self.passlegLongValue)
        self.passlegShortgPos = int(self.passlegShortgPos)
        self.passlegShortValue = float(self.passlegShortValue)

        self.profitloss = float(self.profitloss)

    #----------------------------------------------------------------------
    def addActiveLeg(self, leg):
        """添加主动腿"""
        self.activeLeg = leg
    
    #----------------------------------------------------------------------
    def addPassiveLeg(self, leg):
        """添加被动腿"""
        self.passiveLegs.append(leg)
        
        
    
    