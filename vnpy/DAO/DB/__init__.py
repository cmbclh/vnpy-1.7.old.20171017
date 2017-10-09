##-*-coding: utf-8;-*-##
import sys
#sys.path.append('D:\\tr\\vnpy-master\\vn.trader\\DAO')
sys.path.append('D:/tr/vnpy-master/vn.trader/DAO')
sys.path.append('../')
import pandas as pd
import pandas.io.sql as pds
from pandas import DataFrame; ##多行插入
from sqlalchemy.sql import text
from sqlalchemy import Table
from sqlalchemy import Column
from DBEngin import DBConnector
from util import *
#import config
from config import VnpyParam#,IndexParam,OriginalParam,RegressionParam
from mysql import connector
import pymysql.connections

__Vnpy=DBConnector(VnpyParam)
#__Original=DBConnector(OriginalParam)
#__Index=DBConnector(IndexParam)
#__Regression=DBConnector(RegressionParam)
__dbdict={
        "vnpy":__Vnpy
    }
__option={
    'index':'index',
    'unique':'unique',
    'primary key':'primary key'
}
def __getTable(database,tableName):
    return Table(tableName,__dbdict.get(database).metadata,autoload=True)

def __initTable(database,tableName,columns):
    return Table(tableName,__dbdict.get(database).metadata,*columns)

def __session(database):
    return __dbdict.get(database).session()

def __permission(database):
    if database=='orig':
        raise Exception(u'该接口无权对原始库进行操作')

def query(database,sql):
    if replaceMoreSpace(sql.strip().lower()).find('select') != 0:
        raise Exception(u"sql语句有误")
    return pds.read_sql(sql,__dbdict.get(database).engine)

def update(database,sql):
    __permission(database)
    if replaceMoreSpace(sql.strip().lower()).find('update') != 0:
        raise Exception(u"sql语句有误")
    with __session(database) as s:
        s.execute(text(sql))

def insert(database,tableName,data):
    __permission(database)
    pds.to_sql(data,replaceSpace(tableName),__dbdict.get(database).engine,if_exists='append',index=False)

def truncate(database,tableName):
    __permission(database)
    sql = r'truncate %s ' %  replaceSpace(tableName)
    with __session(database) as s:
        s.execute(text(sql))

def deleteData(database,sql):
    __permission(database)
    if replaceMoreSpace(sql.strip().lower()).find('delete from') != 0:
        raise Exception(u"sql语句有误")
    with __session(database) as s:
        s.execute(text(sql))

def dropTable(database,tableName):
    __permission(database)
    sql = r"drop table %s" % replaceSpace(tableName)
    with __session(database) as s:
        s.execute(text(sql))

def createTable(database,tableName,columns):
    __permission(database)
    for c in columns:
        if not isinstance(c,Column):
            raise Exception(u'columns序列中的元素只能为sqlalchemy.Column类型')
    __initTable(database,replaceSpace(tableName),columns).create()

def createIndex(database,tableName,columns,indexType,indexName):
    __permission(database)
    if not __option.has_key(indexType.strip().lower()):
        raise  Exception(u"非法指令")
    if indexType=='primary key':
        indexName=""
    elif indexName is None:
        raise Exception(u"执行普通索引或唯一索引创建时，indexName必须传值")
    sql = r"alter table %s add %s %s(%s)" % (replaceSpace(tableName),__option.get(indexType),replaceSpace(indexName),replaceSpace(','.join(columns)))
    with __session(database) as s:
        s.execute(text(sql))

def dropIndex(database,tableName,indexType,indexName):
    __permission(database)
    if not __option.has_key(indexType.strip().lower()):
        raise Exception(u"非法指令")
    if indexType == 'primary key':
        indexName = ""
    elif indexName is None:
        raise Exception(u"执行普通索引或唯一索引创建时，indexName必须传值")
    else:
        indexType='index'
    sql = r"alter table %s drop %s %s" % (tableName, __option.get(indexType), indexName)
    with __session(database) as s:
        s.execute(text(sql))

def isTableExist(dabtabase,tableName):
    sql = "show tables like '%s'" % replaceSpace(tableName)
    with __session(dabtabase) as s:
        rs = s.execute(text(sql))
    return False if ((rs is None) or (rs.rowcount<1)) else True

def logger(status,operator,error_message,start_time,end_time):
    sql = r"insert into job_calculation_log (STATUS,OPERATOR,ERROR_MESSAGE,STATR_TIMESTAMP,END_TIMESTAMP) values ('%s','%s','%s','%s','%s')" % (status,operator,error_message,start_time,end_time)
    with __session("index") as s:
        s.execute(text(sql))