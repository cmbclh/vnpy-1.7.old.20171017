##-*-coding: utf-8;-*-##
import DB
from DB import util
import pymysql

__doc__='''
    vnpy为量化库，
    orig为原始库，
    index为指标库，
    dev为回测库
'''
def getData(database, tableName, startDate, endDate, orderBy="transdate",reverse=True):
    sql = r'select * from %s where transdate>=%s and transdate<=%s order by %s %s'% (util.replaceSpace(tableName),
                                                                                     util.replaceSpace(startDate),
                                                                                     util.replaceSpace(endDate),
                                                                                     orderBy,
                                                                                     'DESC' if reverse else 'ASC')
    return DB.query(database,sql)

def getPagedData(database, tableName, pageNo=-1, pageSize=200, orderBy=None,reverse=True):
    sql = r'select * from %s'% util.replaceSpace(tableName)
    if orderBy!=None:
        sql=sql+' order by %s %s ' % (util.replaceSpace(orderBy),'DESC' if reverse else 'ASC')
    if pageNo!=-1:
        sql=sql+r' limit %d,%d' % (pageNo*pageSize,pageSize)
    return DB.query(database,sql)

def getDataBySQL(database,sql):
    return DB.query(database, sql)

def writeData(database,tableName,data,append=True):
    '''暂时不支持清空表和插入数据在同一个数据库事务中进行'''
    if append:
        DB.insert(database, tableName, data)
    else:
        DB.truncate(database, tableName)
        DB.insert(database, tableName, data)

def updateData(database,sql):
    return DB.update(database,sql)

def createTable(database,tableName,columns):
    DB.createTable(database, tableName, columns)

def dropTable(database,tableName):
    DB.dropTable(database, tableName)

def createIndexOnTable(database,tableName,columns,indexType='index',indexName=None):
    DB.createIndex(database,tableName,columns,indexType,indexName)

def dropIndexOnTable(database,tableName,indexType='index',indexName=None):
    DB.dropIndex(database,tableName,indexType,indexName)

def truncateTable(database,tableName):
    DB.truncate(database, tableName)

def deleteData(database,sql):
    DB.deleteData(database,sql)

def isTableExist(dabtabase,tableName):
    return DB.isTableExist(dabtabase,tableName)

def logger(status,operator,error_message,start_time,end_time):
    DB.logger(status,operator,error_message,start_time,end_time)