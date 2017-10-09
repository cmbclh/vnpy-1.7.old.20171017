# encoding: UTF-8

import json
import shelve
import sys
import traceback

import pandas as pd

from vnpy.event import Event
from vnpy.DAO import *
from vnpy.trader.vtConstant import (DIRECTION_LONG, DIRECTION_SHORT,
                                    OFFSET_OPEN, OFFSET_CLOSE,
                                    PRICETYPE_LIMITPRICE)
from vnpy.trader.vtEvent import (EVENT_TICK, EVENT_TRADE, EVENT_POSITION,
                                 EVENT_TIMER, EVENT_ORDER)
from vnpy.trader.vtFunction import getJsonPath, getTempPath
from vnpy.trader.vtObject import (VtSubscribeReq, VtOrderReq,
                                  VtCancelOrderReq, VtLogData)
from vnpy.trader.app.spreadTrading.stAlgo import SniperAlgo
from vnpy.trader.app.spreadTrading.stBase import (StLeg, StSpread, EVENT_SPREADTRADING_TICK,
                     EVENT_SPREADTRADING_POS, EVENT_SPREADTRADING_LOG,
                     EVENT_SPREADTRADING_ALGO, EVENT_SPREADTRADING_ALGOLOG)

sys.path.append("..")


########################################################################
class StDataEngine(object):
    """价差数据计算引擎"""
    settingFileName = 'ST_setting.json'
    settingFilePath = getJsonPath(settingFileName, __file__)

    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine):
        """Constructor"""
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine

        # 腿、价差相关字典
        self.legDict = {}  # vtSymbol:StLeg
        self.spreadDict = {}  # name:StSpread
        self.vtSymbolSpreadDict = {}  # vtSymbol:StSpread

        self.registerEvent()

    # ----------------------------------------------------------------------
    def loadSetting(self):
        """加载配置"""
        try:
            with open(self.settingFilePath) as f:
                l = json.load(f)

                for setting in l:
                    result, msg = self.createSpread(setting)
                    self.writeLog(msg)

                self.writeLog(u'价差配置加载完成')
        except:
            content = u'价差配置加载出错，原因：' + traceback.format_exc()
            self.writeLog(content)

    # ----------------------------------------------------------------------
    def saveSetting(self):
        """保存配置"""
        with open(self.settingFilePath) as f:
            pass

    # ----------------------------------------------------------------------
    def createSpread(self, setting):
        """创建价差"""
        result = False
        msg = ''

        # 检查价差重名
        if setting['name'] in self.spreadDict:
            msg = u'%s价差存在重名' % setting['name']
            return result, msg

        # 检查腿是否已使用
        l = []
        l.append(setting['activeLeg']['vtSymbol'])
        for d in setting['passiveLegs']:
            l.append(d['vtSymbol'])

        for vtSymbol in l:
            if vtSymbol in self.vtSymbolSpreadDict:
                existingSpread = self.vtSymbolSpreadDict[vtSymbol]
                msg = u'%s合约已经存在于%s价差中' % (vtSymbol, existingSpread.name)
                return result, msg

        # 创建价差
        spread = StSpread()
        spread.name = setting['name']
        self.spreadDict[spread.name] = spread

        # 创建主动腿
        activeSetting = setting['activeLeg']

        activeLeg = StLeg()
        activeLeg.vtSymbol = str(activeSetting['vtSymbol'])
        activeLeg.ratio = float(activeSetting['ratio'])
        activeLeg.multiplier = float(activeSetting['multiplier'])
        activeLeg.payup = int(activeSetting['payup'])

        spread.addActiveLeg(activeLeg)
        self.legDict[activeLeg.vtSymbol] = activeLeg
        self.vtSymbolSpreadDict[activeLeg.vtSymbol] = spread

        self.subscribeMarketData(activeLeg.vtSymbol)

        # 创建被动腿
        passiveSettingList = setting['passiveLegs']
        passiveLegList = []

        for d in passiveSettingList:
            passiveLeg = StLeg()
            passiveLeg.vtSymbol = str(d['vtSymbol'])
            passiveLeg.ratio = float(d['ratio'])
            passiveLeg.multiplier = float(d['multiplier'])
            passiveLeg.payup = int(d['payup'])

            spread.addPassiveLeg(passiveLeg)
            self.legDict[passiveLeg.vtSymbol] = passiveLeg
            self.vtSymbolSpreadDict[passiveLeg.vtSymbol] = spread

            self.subscribeMarketData(passiveLeg.vtSymbol)

            # 初始化价差
        spread.initSpread()

        self.putSpreadTickEvent(spread)
        self.putSpreadPosEvent(spread)

        # 返回结果
        result = True
        msg = u'%s价差创建成功' % spread.name
        return result, msg

    # ----------------------------------------------------------------------
    def processTickEvent(self, event):
        """处理行情推送"""
        # 检查行情是否需要处理
        tick = event.dict_['data']
        if tick.vtSymbol not in self.legDict:
            return

        # 更新腿价格
        leg = self.legDict[tick.vtSymbol]
        leg.bidPrice = tick.bidPrice1
        leg.askPrice = tick.askPrice1
        leg.bidVolume = tick.bidVolume1
        leg.askVolume = tick.askVolume1

        # 更新价差价格
        spread = self.vtSymbolSpreadDict[tick.vtSymbol]
        spread.calculatePrice()

        # 发出事件
        self.putSpreadTickEvent(spread)

    # ----------------------------------------------------------------------
    def putSpreadTickEvent(self, spread):
        """发出价差行情更新事件"""
        event1 = Event(EVENT_SPREADTRADING_TICK + spread.name)
        event1.dict_['data'] = spread
        self.eventEngine.put(event1)

        event2 = Event(EVENT_SPREADTRADING_TICK)
        event2.dict_['data'] = spread
        self.eventEngine.put(event2)

    # ----------------------------------------------------------------------
    def processTradeEvent(self, event):
        """处理成交推送"""
        # 检查成交是否需要处理
        trade = event.dict_['data']
        if trade.vtSymbol not in self.legDict:
            return

        # 更新腿持仓
        leg = self.legDict[trade.vtSymbol]
        direction = trade.direction
        offset = trade.offset

        if direction == DIRECTION_LONG:
            if offset == OFFSET_OPEN:
                leg.longPos += trade.volume
            else:
                leg.shortPos -= trade.volume
        else:
            if offset == OFFSET_OPEN:
                leg.shortPos += trade.volume
            else:
                leg.longPos -= trade.volume
        leg.netPos = leg.longPos - leg.shortPos

        # 更新价差持仓
        spread = self.vtSymbolSpreadDict[trade.vtSymbol]
        spread.calculatePos()

        # 推送价差持仓更新
        event1 = Event(EVENT_SPREADTRADING_POS + spread.name)
        event1.dict_['data'] = spread
        self.eventEngine.put(event1)

        event2 = Event(EVENT_SPREADTRADING_POS)
        event2.dict_['data'] = spread
        self.eventEngine.put(event2)

    # ----------------------------------------------------------------------
    def processPosEvent(self, event):
        """处理持仓推送"""
        # 检查持仓是否需要处理
        pos = event.dict_['data']
        if pos.vtSymbol not in self.legDict:
            return

        # 更新腿持仓
        leg = self.legDict[pos.vtSymbol]
        direction = pos.direction

        if direction == DIRECTION_LONG:
            leg.longPos = pos.position
        else:
            leg.shortPos = pos.position
        leg.netPos = leg.longPos - leg.shortPos

        # 更新价差持仓
        spread = self.vtSymbolSpreadDict[pos.vtSymbol]
        spread.calculatePos()

        # 推送价差持仓更新
        self.putSpreadPosEvent(spread)

    # ----------------------------------------------------------------------
    def putSpreadPosEvent(self, spread):
        """发出价差持仓事件"""
        event1 = Event(EVENT_SPREADTRADING_POS + spread.name)
        event1.dict_['data'] = spread
        self.eventEngine.put(event1)

        event2 = Event(EVENT_SPREADTRADING_POS)
        event2.dict_['data'] = spread
        self.eventEngine.put(event2)


        # ----------------------------------------------------------------------

    def registerEvent(self):
        """"""
        self.eventEngine.register(EVENT_TICK, self.processTickEvent)
        self.eventEngine.register(EVENT_TRADE, self.processTradeEvent)
        self.eventEngine.register(EVENT_POSITION, self.processPosEvent)

    # ----------------------------------------------------------------------
    def subscribeMarketData(self, vtSymbol):
        """订阅行情"""
        contract = self.mainEngine.getContract(vtSymbol)
        if not contract:
            self.writeLog(u'订阅行情失败，找不到该合约%s' % vtSymbol)
            return

        req = VtSubscribeReq()
        req.symbol = contract.symbol
        req.exchange = contract.exchange

        self.mainEngine.subscribe(req, contract.gatewayName)

    # ----------------------------------------------------------------------
    def writeLog(self, content):
        """发出日志"""
        log = VtLogData()
        log.logContent = content

        event = Event(EVENT_SPREADTRADING_LOG)
        event.dict_['data'] = log
        self.eventEngine.put(event)

    # ----------------------------------------------------------------------
    def getAllSpreads(self):
        """获取所有的价差"""
        return self.spreadDict.values()


        ########################################################################


class StAlgoEngine(object):
    """价差算法交易引擎"""
    algoFileName = 'SpreadTradingAlgo.vt'
    algoFilePath = getTempPath(algoFileName)

    # ----------------------------------------------------------------------
    def __init__(self, dataEngine, mainEngine, eventEngine):
        """Constructor"""
        self.dataEngine = dataEngine
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine

        self.algoDict = {}  # spreadName:algo
        self.vtSymbolAlgoDict = {}  # vtSymbol:algo

        self.registerEvent()

    # ----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        self.eventEngine.register(EVENT_SPREADTRADING_TICK, self.processSpreadTickEvent)
        self.eventEngine.register(EVENT_SPREADTRADING_POS, self.processSpreadPosEvent)
        self.eventEngine.register(EVENT_TRADE, self.processTradeEvent)
        self.eventEngine.register(EVENT_ORDER, self.processOrderEvent)
        self.eventEngine.register(EVENT_TIMER, self.processTimerEvent)

    # ----------------------------------------------------------------------
    # 成交回报后持仓处理
    def updatePosition(self, trade):
        if trade.vtSymbol not in self.vtSymbolAlgoDict:
            return
        sniperAlgo = SniperAlgo(self.vtSymbolAlgoDict[trade.vtSymbol])
        # 取出合约对应的委托单列表
        orderIdList = sniperAlgo.legOrderDict[trade.vtSymbol]
        # 该笔成交是该算法发出的委托
        if trade.vtOrderID in orderIdList:
            spreadName = self.sniperAlgo.spreadName
            # 根据客户、策略、合约从数据库中取出持仓信息
            qrySql = 'select LONG_POSITION, TODAY_LONG, LONG_OPEN_AVG_PRICE, SHORT_POSITION, TODAY_SHORT, SHORT_OPEN_AVG_PRICE' \
                     'from defer_real_hold where BROKER_ID = %s and EXCH_ID = %s and SYMBOL = %s and STRATAGE = %s' % (
                         trade.brokerID,
                         trade.exch_id, trade.symbol, spreadName)
            retData = getDataBySQL('vnpy', qrySql)
            posData = retData.irow(0)  # 根据以上条件查询出的默认持仓只有一条记录
            # 没有持仓记录，首次交易
            if not posData:
                posData.longPosition = EMPTY_INT
                posData.longToday = EMPTY_INT
                posData.longOpenAverPrice = EMPTY_FLOAT
                posData.shortPosition = EMPTY_INT
                posData.shortToday = EMPTY_INT
                posData.shortOpenAverPrice = EMPTY_INT
            if trade.direction == DIRECTION_LONG:
                # 多方开仓，则对应多头的持仓和今仓增加
                if trade.offset == OFFSET_OPEN:
                    posData.longOpenAverPrice = (
                                                    posData.longOpenAverPrice * posData.longPosition + trade.volume * trade.price) / (
                                                    posData.longPosition + trade.volume)
                    posData.longPosition += trade.volume
                    posData.longToday += trade.volume
                elif trade.offset == OFFSET_CLOSETODAY:  # 先开先平以后考虑
                    # 公式
                    posData.shortOpenAverPrice = (
                                                     posData.shortOpenAverPrice * posData.shortPosition - trade.volume * trade.price) / (
                                                     posData.shortPosition - trade.volume)
                    posData.shortPosition -= trade.volume
                    posData.shortToday -= trade.volume
            else:
                # 空方开仓，则对应空头的持仓和今仓增加
                if trade.offset == OFFSET_OPEN:
                    posData.shortOpenAverPrice = (
                                                     posData.shortOpenAverPrice * posData.shortPosition + trade.volume * trade.price) / (
                                                     posData.shortPosition + trade.volume)
                    posData.shortPosition += trade.volume
                    posData.shortToday += trade.volume
                elif trade.offset == OFFSET_CLOSETODAY:
                    posData.longOpenAverPrice = (
                                                    posData.longOpenAverPrice * posData.longPosition - trade.volume * trade.price) / (
                                                    posData.longPosition - trade.volume)
                    posData.longPosition -= trade.volume
                    posData.longToday -= trade.volume

            # 更新defer_real_hold表
            updateSql = 'update defer_real_hold set LONG_POSITION = %s, TODAY_LONG = %s, LONG_OPEN_AVG_PRICE = %s,' \
                        'SHORT_POSITION = %s, TODAY_SHORT = %s, SHORT_OPEN_AVG_PRICE = %s where BROKER_ID = %s and EXCH_ID = %s and SYMBOL = %s and STRATAGE = %s' % (
                            posData.longPosition, posData.longToday, posData.longOpenAverPrice, posData.shortPosition,
                            posData.shortToday, posData.shortOpenAverPrice,
                            trade.brokerID, trade.exch_id, trade.symbol, spreadName)
            try:
                updateData('vnpy', updateSql)
            except Exception as e:
                self.writeLog(u"更新客户持仓信息出错，错误信息：%s" % str(e.message))

    # 成交回报入库
    def handleTradeData(self, trade):
        if trade.vtSymbol not in self.vtSymbolAlgoDict:
            return
        sniperAlgo = SniperAlgo(self.vtSymbolAlgoDict[trade.vtSymbol])
        # 取出合约对应的委托单列表
        orderIdList = sniperAlgo.legOrderDict[trade.vtSymbol]
        # 该笔成交是该算法发出的委托
        if trade.vtOrderID in orderIdList:
            spreadName = sniperAlgo.spreadName
            DEFER_DONE_COLUMNS = ['VT_TRADE_ID', 'VT_ORDER_ID', 'TRADE_DATE', 'TRADE_TIME', 'USER_ID',
                                  'BROKER_ID', 'OPER_CODE', 'SYMBOL', 'EXCH_ID', 'TRADE_PRICE', 'DONE_QTY',
                                  'BS_FLAG', 'EO_FLAG', 'STRATAGE']
            tradedata = [trade.vtTradeID, trade.vtOrderID, '', trade.tradeTime, '',
                         trade.brokerID, '', trade.symbol, trade.exch_id, trade.price, trade.volume,
                         trade.direction, trade.offset, spreadName]
            d = pd.DataFrame([tradedata], columns=DEFER_DONE_COLUMNS)
            print("开始写入DEFER_DONE")
            try:
                writeData('vnpy', 'DEFER_DONE', d)
                print("写入DEFER_DONE结束了")
            except Exception as e:
                self.writeLog(u"增量写入数据时发生了错误，错误信息：%s" % str(e.message))
                print("写入DEFER_DONE报错")

    # 委托单入库处理
    def handleOrder(self, vtSymbol, orderReq):
        #orderReq = VtOrderReq()
        spreadName = self.vtSymbolAlgoDict[vtSymbol].spreadName
        DEFER_ENTRUST_COLUMNS = ['VT_ORDER_ID', 'ENTRUST_DATE', 'ENTRUST_TIME', 'USER_ID',
                                 'BROKER_ID', 'OPER_CODE', 'SYMBOL', 'EXCH_ID', 'ENTRUST_PRICE',
                                 'ENTRUST_QTY', 'PRODUCT_CLASS', 'CURRENCY_CODE', 'PRICE_TYPE', 'BS_FLAG',
                                 'EO_FLAG', 'ENTRUST_STATUS', 'STRATAGE']
        orderData = ['', '', '', '', '', '', orderReq.symbol, orderReq.exchange, orderReq.price, orderReq.volume,
                     '', '', '', orderReq.direction, orderReq.offset, '', spreadName]
        d = pd.DataFrame([orderData], columns=DEFER_ENTRUST_COLUMNS)
        print("开始写入DEFER_ENTRUST中")
        try:
            writeData('vnpy', 'DEFER_ENTRUST', d)
            # common.logger.info(u"写入数据%s" % (d.max))
            print("写入DEFER_ENTRUST结束了")
        except Exception as e:
            self.writeLog(u"增量写入数据时发生了错误，错误信息：%s" % str(e.message))
            print("写入DEFER_ENTRUST报错")

    # 委托推送入库处理
    def handleOrderBack(self, order,event):
        if order.vtSymbol not in self.vtSymbolAlgoDict:
            return

        spread = event.dict_['data']
        sniperAlgo = SniperAlgo(self.vtSymbolAlgoDict[order.vtSymbol],spread)
        # 取出合约对应的委托单列表
        orderIdList = sniperAlgo.legOrderDict[order.vtSymbol]
        # 该笔委托回报是该算法发出的委托
        if order.vtOrderID in orderIdList:
            DEFER_ENTRUST_RTN_COLUMNS = ['VT_ORDER_ID', 'ENTRUST_DATE', 'ENTRUST_TIME', 'CANCEL_TIME',
                                         'USER_ID',
                                         'BROKER_ID', 'OPER_CODE', 'SYMBOL', 'EXCH_ID', 'ENTRUST_PRICE',
                                         'ENTRUST_QTY',
                                         'PRODUCT_CLASS', 'CURRENCY_CODE', 'PRICE_TYPE', 'BS_FLAG',
                                         'EO_FLAG', 'ENTRUST_STATUS', 'STRATAGE']
            ordertn = [order.vtOrderID, '', '', '', '',
                       order.brokerID, '', order.symbol, order.exch_id, order.price, order.totalVolume,
                       '', '', '', order.direction, order.offset, '', sniperAlgo.spreadName]
            d = pd.DataFrame([ordertn], columns=DEFER_ENTRUST_RTN_COLUMNS)
            print("开始写入DEFER_ENTRUST_RTN中")
            try:
                writeData('vnpy', 'DEFER_ENTRUST_RTN', d)
                # common.logger.info(u"写入数据%s" % (d.max))
                print("写入DEFER_ENTRUST_RTN结束了")
            except Exception as e:
                self.writeLog(u"增量写入数据时发生了错误，错误信息：%s" % str(e.message))
                print("写入DEFER_ENTRUST_RTN报错")

    # ----------------------------------------------------------------------
    def processSpreadTickEvent(self, event):
        """处理价差行情事件"""
        spread = event.dict_['data']

        algo = self.algoDict.get(spread.name, None)
        if algo:
            algo.updateSpreadTick(spread)

    # ----------------------------------------------------------------------
    def processSpreadPosEvent(self, event):
        """处理价差持仓事件"""
        spread = event.dict_['data']

        algo = self.algoDict.get(spread.name, None)
        if algo:
            algo.updateSpreadPos(spread)

    # ----------------------------------------------------------------------
    def processTradeEvent(self, event):
        """处理成交事件"""
        trade = event.dict_['data']
        # 持仓处理、成交入库
        self.updatePosition(trade)
        self.handleTradeData(trade)

        algo = self.vtSymbolAlgoDict.get(trade.vtSymbol, None)
        if algo:
            algo.updateTrade(trade)

    # ----------------------------------------------------------------------
    def processOrderEvent(self, event):
        """处理委托事件"""
        order = event.dict_['data']
        self.handleOrderBack(order,event)

        algo = self.vtSymbolAlgoDict.get(order.vtSymbol, None)

        if algo:
            algo.updateOrder(order)

    # ----------------------------------------------------------------------
    def processTimerEvent(self, event):
        """"""
        for algo in self.algoDict.values():
            algo.updateTimer()

    # ----------------------------------------------------------------------
    def sendOrder(self, vtSymbol, direction, offset, price, volume, payup=0):
        """发单"""
        contract = self.mainEngine.getContract(vtSymbol)
        if not contract:
            return ''

        req = VtOrderReq()
        req.symbol = contract.symbol
        req.exchange = contract.exchange
        req.direction = direction
        req.offset = offset
        req.volume = int(volume)
        req.priceType = PRICETYPE_LIMITPRICE

        if direction == DIRECTION_LONG:
            req.price = price + payup * contract.priceTick
        else:
            req.price = price - payup * contract.priceTick

        vtOrderID = self.mainEngine.sendOrder(req, contract.gatewayName)
        # 委托单入库处理
        self.handleOrder(vtSymbol, req)

        return vtOrderID

    # ----------------------------------------------------------------------
    def cancelOrder(self, vtOrderID):
        """撤单"""
        order = self.mainEngine.getOrder(vtOrderID)
        if not order:
            return

        req = VtCancelOrderReq()
        req.symbol = order.symbol
        req.exchange = order.exchange
        req.frontID = order.frontID
        req.sessionID = order.sessionID
        req.orderID = order.orderID

        self.mainEngine.cancelOrder(req, order.gatewayName)

    # ----------------------------------------------------------------------
    def buy(self, vtSymbol, price, volume, payup=0):
        """买入"""
        vtOrderID = self.sendOrder(vtSymbol, DIRECTION_LONG, OFFSET_OPEN, price, volume, payup)
        l = []

        if vtOrderID:
            l.append(vtOrderID)

        return l

    # ----------------------------------------------------------------------
    def sell(self, vtSymbol, price, volume, payup=0):
        """卖出"""
        vtOrderID = self.sendOrder(vtSymbol, DIRECTION_SHORT, OFFSET_CLOSE, price, volume, payup)
        l = []

        if vtOrderID:
            l.append(vtOrderID)

        return l

    # ----------------------------------------------------------------------
    def short(self, vtSymbol, price, volume, payup=0):
        """卖空"""
        vtOrderID = self.sendOrder(vtSymbol, DIRECTION_SHORT, OFFSET_OPEN, price, volume, payup)
        l = []

        if vtOrderID:
            l.append(vtOrderID)

        return l

    # ----------------------------------------------------------------------
    def cover(self, vtSymbol, price, volume, payup=0):
        """平空"""
        vtOrderID = self.sendOrder(vtSymbol, DIRECTION_LONG, OFFSET_CLOSE, price, volume, payup)
        l = []

        if vtOrderID:
            l.append(vtOrderID)

        return l

    # ----------------------------------------------------------------------
    def putAlgoEvent(self, algo):
        """发出算法状态更新事件"""
        event = Event(EVENT_SPREADTRADING_ALGO + algo.name)
        self.eventEngine.put(event)

    # ----------------------------------------------------------------------
    def writeLog(self, content):
        """输出日志"""
        log = VtLogData()
        log.logContent = content

        event = Event(EVENT_SPREADTRADING_ALGOLOG)
        event.dict_['data'] = log

        self.eventEngine.put(event)

    # ----------------------------------------------------------------------
    def saveSetting(self):
        """保存算法配置"""
        setting = {}
        for algo in self.algoDict.values():
            setting[algo.spreadName] = algo.getAlgoParams()

        f = shelve.open(self.algoFilePath)
        f['setting'] = setting
        f.close()

    # ----------------------------------------------------------------------
    def loadSetting(self):
        """加载算法配置"""
        # 创建算法对象
        l = self.dataEngine.getAllSpreads()
        for spread in l:
            algo = SniperAlgo(self, spread)
            self.algoDict[spread.name] = algo

            # 保存腿代码和算法对象的映射
            for leg in spread.allLegs:
                self.vtSymbolAlgoDict[leg.vtSymbol] = algo

        # 加载配置
        f = shelve.open(self.algoFilePath)
        setting = f.get('setting', None)
        f.close()

        if not setting:
            return

        for algo in self.algoDict.values():
            if algo.spreadName in setting:
                d = setting[algo.spreadName]
                algo.setAlgoParams(d)

    # ----------------------------------------------------------------------
    def stopAll(self):
        """停止全部算法"""
        for algo in self.algoDict.values():
            algo.stop()

    # ----------------------------------------------------------------------
    def startAlgo(self, spreadName):
        """启动算法"""
        algo = self.algoDict[spreadName]
        algoActive = algo.start()
        return algoActive

    # ----------------------------------------------------------------------
    def stopAlgo(self, spreadName):
        """停止算法"""
        algo = self.algoDict[spreadName]
        algoActive = algo.stop()
        return algoActive

    # ----------------------------------------------------------------------
    def getAllAlgoParams(self):
        """获取所有算法的参数"""
        return [algo.getAlgoParams() for algo in self.algoDict.values()]

    # ----------------------------------------------------------------------
    def setAlgoBuyPrice(self, spreadName, buyPrice):
        """设置算法买开价格"""
        algo = self.algoDict[spreadName]
        algo.setBuyPrice(buyPrice)

    # ----------------------------------------------------------------------
    def setAlgoSellPrice(self, spreadName, sellPrice):
        """设置算法卖平价格"""
        algo = self.algoDict[spreadName]
        algo.setSellPrice(sellPrice)

    # ----------------------------------------------------------------------
    def setAlgoShortPrice(self, spreadName, shortPrice):
        """设置算法卖开价格"""
        algo = self.algoDict[spreadName]
        algo.setShortPrice(shortPrice)

    # ----------------------------------------------------------------------
    def setAlgoCoverPrice(self, spreadName, coverPrice):
        """设置算法买平价格"""
        algo = self.algoDict[spreadName]
        algo.setCoverPrice(coverPrice)

    # ----------------------------------------------------------------------
    def setAlgoMode(self, spreadName, mode):
        """设置算法工作模式"""
        algo = self.algoDict[spreadName]
        algo.setMode(mode)

    # ----------------------------------------------------------------------
    def setAlgoMaxOrderSize(self, spreadName, maxOrderSize):
        """设置算法单笔委托限制"""
        algo = self.algoDict[spreadName]
        algo.setMaxOrderSize(maxOrderSize)

    # ----------------------------------------------------------------------
    def setAlgoMaxPosSize(self, spreadName, maxPosSize):
        """设置算法持仓限制"""
        algo = self.algoDict[spreadName]
        algo.setMaxPosSize(maxPosSize)


########################################################################
class StEngine(object):
    """价差引擎"""

    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine):
        """Constructor"""
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine

        self.dataEngine = StDataEngine(mainEngine, eventEngine)
        self.algoEngine = StAlgoEngine(self.dataEngine, mainEngine, eventEngine)

    # ----------------------------------------------------------------------
    def init(self):
        """初始化"""
        self.dataEngine.loadSetting()
        self.algoEngine.loadSetting()

    # ----------------------------------------------------------------------
    def stop(self):
        """停止"""
        self.dataEngine.saveSetting()

        self.algoEngine.stopAll()
        self.algoEngine.saveSetting()




