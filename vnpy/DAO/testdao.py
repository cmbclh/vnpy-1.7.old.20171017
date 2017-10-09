##-*-coding: utf-8;-*-##
import sys
#sys.path.append('D:\\tr\\vnpy-master\\vn.trader\\DAO')
sys.path.append('D:/tr/vnpy-master/vn.trader/common')
import common
import pandas as pd
from sqlalchemy import Column
from sqlalchemy import DECIMAL
from sqlalchemy import Integer
from sqlalchemy import String
from __init__ import  *

if __name__=='__main__':
    #创建数据库表
    columns=[Column('date',String(8),primary_key=True),Column('code',String(8),nullable=False,primary_key=True),Column('name',String(50)),Column('close',DECIMAL(12,4)),Column('open',DECIMAL(12,4))]
    common.logger.info(u"执行数据库表%s的创建，列信息：%s" % ("test_table", str(columns)))
    try:
        #caiiasdata.createTable('index','test_table',columns)
        createTable('vnpy', 'test_table', columns)
    except Exception as e:
        common.logger.error(u"创建指标数据库中的表%s发生了错误，错误信息：%s" % ("test_table", str(e.message)))

    #创建/删除数据库索引
    #caiiasdata.createIndexOnTable('index','test_table',list(['code']),'index','test_index_on_table')
    #caiiasdata.createIndexOnTable('index','test_table',list(['name']),'unique','test_table_unique_index')
    #caiiasdata.dropIndexOnTable('index','test_table','primary key')
    #caiiasdata.createIndexOnTable('index','test_table',list(['date','code']),'primary key')
    #caiiasdata.dropIndexOnTable('index','test_table','unique','test_table_unique_index')
    #caiiasdata.dropIndexOnTable('index', 'test_table', 'index', 'test_index_on_table')
    #数据查询
    for i in range(100):
        data = getPagedData('orig','ch_cihdquote',i,2000,orderBy='tdate',reverse=True)

        #dataframe操作样例
        data = data[['tdate','symbol','sname','tclose','topen']]
        data.rename(columns={'tdate':'date','symbol':'code','sname':'name','tclose':'close','topen':'open'},inplace=True)

        # 数据写入-增量
        try:
            writeData('index','test_table',data)
            common.logger.error(u"写入数据%s-%s" % (str(i*2000),str(i*2000+1999)))
        except Exception as e:
            common.logger.error(u"增量写入数据时发生了错误，错误信息：%s" % str(e.message))
    #数据写入-全量
    #caiiasdata.writeData('index','test_table',data,append=False)

    #新表的数据查询
    #print caiiasdata.getPagedData('index','test_table')
    '''
      date    code          name     close      open
    0  20170421  W00002        纳斯达克指数  5910.521  5919.024
    1  20170421  W00003         标普500  2348.690  2354.740
    2  20170422  H30085  一财理财指数(三个月内)     4.466       NaN
    3  20170423  H30085  一财理财指数(三个月内)     4.466       NaN
    4  20170424  H30085  一财理财指数(三个月内)     4.466       NaN
    '''

    #数据库表清空
    #caiiasdata.truncateTable('index','test_table')

    #数据库写入（全量）异常处理
    # try:
    #     caiiasdata.writeData('index','test_table',data,append=True)
    # except Exception as e:
    #     common.logger.error(u"全量写入数据时发生了错误，错误信息：%s" % str(e.message))
        # caiiasdata.deleteData('index',r"delete from test_table")#若失败的写入操作已写入部分数据，可手动删除。再进行重新写入。
        # # 理论上writeData写入操作已进行事务封装，若失败，则已执行的插入会自动回滚
        # caiiasdata.writeData('index','test_table',data,append=False)

    #数据库表删除
    common.logger.info(u"删除指标数据库中的表%s" % "test_table")
    try:
        #caiiasdata.dropTable('index','test_table')
        dropTable('index', 'test_table')
    except Exception as e:
        common.logger.error(u"删除指标数据库中的表%s发生了错误，错误信息：%s" % ("test_table",str(e.message)))