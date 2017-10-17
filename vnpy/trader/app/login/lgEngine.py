# encoding: UTF-8

'''
本文件中实现了登陆模块：
1. 登陆
2. 登出
3. 注册
'''

import json
import platform

import sys
sys.path.append('../')
#sys.path.append('D:\\tr\\vnpy-master\\vn.trader\\DAO')
sys.path.append('D:\\tr\\vnpy-1.7\\vnpy\\DAO')
sys.path.append('D:\\tr\\vnpy-1.7\\vnpy\\common')
import vnpy.DAO
import vnpy.common
from vnpy.DAO import *

import Tkinter
#from Tkinter import messagebox

from vnpy.event import Event
from vnpy.trader.vtEvent import *
from vnpy.trader.vtFunction import getJsonPath
from vnpy.trader.vtGateway import VtLogData
from vnpy.trader.vtConstant import (EMPTY_INT, EMPTY_FLOAT,EMPTY_STRING, EMPTY_UNICODE,STATUS_CANCELLED)
from vnpy.trader.vtConstant import *
########################################################################
class LoginEngine(object):
    """登陆引擎"""
    settingFileName = 'Login_setting.json'
    settingFilePath = getJsonPath(settingFileName, __file__)

    name = u'登陆模块'

    #----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine):
        """Constructor"""
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        
        # 绑定自身到主引擎的登陆引擎引用上
        mainEngine.loginEngine = self

        #登陆相关
        self.userId = EMPTY_STRING          # 用户名
        self.password  = EMPTY_STRING       # 密码

        self.loadSetting()
        self.registerEvent()

    #----------------------------------------------------------------------
    def loadSetting(self):
        """读取配置"""
        with open(self.settingFilePath) as f:
            d = json.load(f)

            # 设置登陆参数
            self.userId = d['userid']
            self.password  = d['password']

    #----------------------------------------------------------------------
    def saveSetting(self):
        """保存登陆参数"""
        with open(self.settingFilePath, 'w') as f:
            # 保存风控参数
            d = {}
            d['userid'] = self.userId
            d['password'] = self.password

            # 写入json
            jsonD = json.dumps(d, indent=4)
            f.write(jsonD)

    #----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        pass
        #self.eventEngine.register(EVENT_TRADE, self.updateTrade)
        #self.eventEngine.register(EVENT_TIMER, self.updateTimer)
        #self.eventEngine.register(EVENT_ORDER, self.updateOrder)

    #----------------------------------------------------------------------
    def stop(self):
        """停止"""
        self.saveSetting()
        
