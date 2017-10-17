# encoding: UTF-8

'''
登陆模块相关的GUI控制组件
'''

import sys
sys.path.append('../')
#sys.path.append('D:\\tr\\vnpy-master\\vn.trader\\DAO')
sys.path.append('D:\\tr\\vnpy-1.7\\vnpy\\DAO')
sys.path.append('D:\\tr\\vnpy-1.7\\vnpy\\common')
import vnpy.DAO
import vnpy.common
from vnpy.DAO import *

import pandas as pd

import Tkinter
#from Tkinter import messagebox


from vnpy.trader.app.login.language import text
from vnpy.trader.uiBasicWidget import QtWidgets

TBUSER_COLUMNS = ['user_id','user_name','status','password','branch_no','open_date','cancel_date','passwd_date','op_group','op_rights','reserve1','dep_id','last_logon_date','last_logon_time','last_ip_address','fail_times','fail_date','reserve2','last_fail_ip']


########################################################################
class LoginSpinBox(QtWidgets.QLineEdit):#.QSpinBox):
    """调整参数用的数值框"""

    #----------------------------------------------------------------------
    def __init__(self, value):
        """Constructor"""
        super(LoginSpinBox, self).__init__()

        #self.setMinimum(0)
        #self.setMaximum(1000000)
        
        self.setText(value)
    

########################################################################
class LoginLine(QtWidgets.QFrame):
    """水平分割线"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        super(LoginLine, self).__init__()
        self.setFrameShape(self.HLine)
        self.setFrameShadow(self.Sunken)
    

########################################################################
class LoginEngineManager(QtWidgets.QWidget):
    """风控引擎的管理组件"""

    #----------------------------------------------------------------------
    def __init__(self, loginEngine, eventEngine, parent=None):
        """Constructor"""
        super(LoginEngineManager, self).__init__(parent)
        
        self.loginEngine = loginEngine
        self.eventEngine = eventEngine
        
        self.initUi()

    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        print self
        self.setWindowTitle(text.LOGIN_MANAGER)
        
        # 设置界面
        self.userId = LoginSpinBox(self.loginEngine.userId)
        self.password = LoginSpinBox(self.loginEngine.password)
        
        buttonLogin = QtWidgets.QPushButton(text.LOGIN)
        buttonLogout = QtWidgets.QPushButton(text.LOGOUT)
        buttonSubmit = QtWidgets.QPushButton(text.SUBMIT)

        Label = QtWidgets.QLabel
        grid = QtWidgets.QGridLayout()
        grid.addWidget(Label(text.USERID), 2, 0)
        grid.addWidget(self.userId, 2, 1)
        grid.addWidget(Label(text.PASSWORD), 3, 0)
        grid.addWidget(self.password, 3, 1)
        grid.addWidget(LoginLine(), 4, 0, 1, 2)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(buttonSubmit)
        hbox.addWidget(buttonLogin)
        
        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(grid)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        
        # 连接组件信号
        buttonSubmit.clicked.connect(self.submit)
        buttonLogin.clicked.connect(self.login)
        
        # 设为固定大小
        self.setFixedSize(self.sizeHint())
        
    # ----------------------------------------------------------------------
    def login(self):
        print (u'登陆验证开始self.userId=%s, self.password=%s' % (self.userId, self.password))
        userId = str(self.userId.text())
        password = str(self.password.text())
        print (u'登陆验证开始userId=%s, password=%s' % (userId, password))
        # 根据以下条件查询出的有效用户只有一条记录
        sql = ' SELECT *' \
              ' from tbuser where user_id = \'%s\' and password = \'%s\' and status = 0 ' % (userId, password)

        try:
            ret = vnpy.DAO.getDataBySQL('vnpy', sql)
            if ret.empty :
                print (u'登陆验证失败，用户不存在或密码不正确')
                #QtWidgets.QMessageBox.information(self, "登陆失败",  "用户不存在或密码不正确，请重试！",  QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                QtWidgets.QMessageBox.information(self, text.LOGINERROR,text.LOGINERRORINFO,
                                                  QtWidgets.QMessageBox.Retry)
                #Tkinter.messagebox.showinfo('登陆验证失败，用户不存在或密码不正确')
            else:
                print (u'登陆验证成功')
                QtWidgets.QMessageBox.information(self, text.LOGINSUSS, text.LOGINSUSSINFO, QtWidgets.QMessageBox.Ok)
                self.close()
                #Tkinter.messagebox.showinfo('欢迎')
        except Exception as e:
            print e

    # ----------------------------------------------------------------------
    def logout(self):
        pass

    # ----------------------------------------------------------------------
    def submit(self):
        userId = str(self.userId.text())
        password = str(self.password.text())
        print (u'注册验证开始userId=%s, password=%s' % (userId, password))
        # 根据以下条件查询出的有效用户只有一条记录
        sql = ' SELECT user_id,status' \
              ' from tbuser where user_id = \'%s\' ' % (userId)
        try:
            ret = vnpy.DAO.getDataBySQL('vnpy', sql)
            #若系统中无该用户，则直接插入注册
            if ret.empty:
                print (u'无此客户信息，可直接注册')
                userData = [userId, userId, 0, password, '', 0, 0, 0, '', ' ', ' ', '', 0, 0, '', 0, 0, ' ', '']
                d = pd.DataFrame([userData], columns=TBUSER_COLUMNS)
                try:
                    print("开始写入TBUSER中")
                    vnpy.DAO.writeData('vnpy', 'tbuser', d)
                    print (u'注册成功')
                    QtWidgets.QMessageBox.information(self, text.SUBMIT, text.SUBMITSUSS, QtWidgets.QMessageBox.Ok)
                    self.close()
                except Exception as e1:
                    print (u'注册失败')
                    QtWidgets.QMessageBox.information(self, text.SUBMIT, text.SUBMITFAIL, QtWidgets.QMessageBox.Retry)
                    print e1
            # 若系统中有该用户，则修改状态及密码，激活用户
            else:
                #暂时空
                QtWidgets.QMessageBox.information(self, text.SUBMIT, text.SUBMITFAIL, QtWidgets.QMessageBox.Ok)
                self.close()
        except Exception as e:
            print e
        #QtWidgets.QMessageBox.information(self, text.SUBMIT, text.SUBMITSUSS, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)

    # ----------------------------------------------------------------------
    def closeLoginEngineManager(self):
        self.close()
        pass