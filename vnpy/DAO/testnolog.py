##-*-coding: utf-8;-*-##
import sys
sys.path.append('../')
#sys.path.append('D:\\tr\\vnpy-master\\vn.trader\\DAO')
sys.path.append('D:/tr/vnpy-1.7/vnpy/common')
import pandas as pd
from sqlalchemy import Column
from sqlalchemy import DECIMAL
from sqlalchemy import Integer
from sqlalchemy import String
from __init__ import *
import common

if __name__=='__main__':
    #创建数据库表
    columns=[Column('date',String(8),primary_key=True),Column('code',String(8),nullable=False,primary_key=True),Column('name',String(50)),Column('close',DECIMAL(12,4)),Column('open',DECIMAL(12,4))]
    common.logger.info(u"执行数据库表%s的创建，列信息：%s" % ("test_table", str(columns)))


    try:
        if not isTableExist('vnpy', 'test_table') :
           createTable('vnpy', 'test_table', columns)
           print('DONE')
    except Exception as e:
        common.logger.error(u"创建指标数据库中的表%s发生了错误，错误信息：%s" % ("test_table", str(e.message)))
        print("test")
        print(u"test：%s %s" % ("test_table", str(e.message)))

    print("开始写入")

    #dataframe操作样例
    #data = [['20150101','au1801','黄金','1','2'],['20150101','au1802','黄金2','1','2'],['20150101','au1803','黄金3','1','2']]
    #data.rename(columns={'tdate':'date','symbol':'code','sname':'name','tclose':'close','topen':'open'},inplace=True)

    # dataframe操作样例
    data = ['tdate', 'symbol', 'sname', 'tclose', 'topen']
    #data.rename(columns={'tdate': 'date', 'symbol': 'code', 'sname': 'name', 'tclose': 'close', 'topen': 'open'}, inplace=True)

    datas = [['20150101','au1801','黄金','1','2'],['20150101','au1802','黄金2','1','2'],['20150101','au1803','黄金3','1','2']]

    datas1 = (['20150101','au1801','黄金','1','2'],['20150101','au1802','黄金2','1','2'],['20150101','au1803','黄金3','1','2'])
    #df_datas1 = pd.DataFrame(datas1)
    #df = DataFrame(np.random.randn(4, 5), columns=['A', 'B', 'C', 'D', 'E'])

    order = ['20150107','au1804','黄金','1','4']

    d = pd.DataFrame([ ['20150101','au1804','黄金','1','4'],  ['20150101','au1805','黄金2','1','5'],  ['20150101'    , 'au1806', '黄金3', '1', '6']], columns = ['date', 'code', 'name', 'close', 'open'])
    d = pd.DataFrame([order], columns=['date', 'code', 'name', 'close', 'open'])

    print("开始写入中")
    try:
        writeData('vnpy', 'test_table', d)
        #common.logger.info(u"写入数据%s" % (d.max))
        print("写入结束了")
    except Exception as e:
        common.logger.error(u"增量写入数据时发生了错误，错误信息：%s" % str(e.message))
        print("写入报错")

    #df_datas = pd.DataFrame(datas,data)

    #X = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
   # X_df = pd.DataFrame(X)

    #df = pd.DataFrame(dict((c, [1, 2, 3]) for c in ['a', 'b', 'c']))
    #df.set_index(['a', 'b', 'c'], inplace=True)


#    for d in df_datas1:
#        print("开始写入中")
#        try:
#            writeData('vnpy','testtable',d)
#            common.logger.info(u"写入数据%s" % (d.__str__()))
#            print(u"写入数据%d" % d.count(d))
#            print("开始写入了")
#        except Exception as e:
#            common.logger.error(u"增量写入数据时发生了错误，错误信息：%s" % str(e.message))
#            print("写入报错")
#