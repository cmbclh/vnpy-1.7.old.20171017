##-*-coding: utf-8;-*-##
import common
import datetime
import caiiasdata
import re
import setlog
import pandas as pd
from common.dateutils import months_ago
from common.dateutils import days_ago
from common.dateutils import days_after
from common.dateutils import strtodate
from datetime import date

import multiprocessing

setlog.setup_logging()

class Operator(object):
    '''
    指标的基类，所有算子必须继承该类，并实现calculate_one_day 方法
    '''

    table_name = None
    table_columns = None
    org_table_list = None
    org_data = None
    result_data = None
    cal_start_date = None
    cal_end_date = None
    #model_list = None
    DEFAULT_CAL_START_DATE = '20170101'

    STATUS_RUNNING  = 100
    STATUS_SUCCESS  = 200
    STATUS_FAILED   = 500

    def __init__(self):
            #默认执行的开始日期
            if self.cal_start_date in (None, '', '0'):
                self.cal_start_date = self.get_start_date()
                self.cal_start_date = days_after(datetime.datetime.strptime(self.cal_start_date, '%Y%m%d'), 1)  # 当前数据库最大日期后一日

            #默认执行的截止日期
            if self.cal_end_date in (None, '', '0'):
                #self.cal_end_date = datetime.date.today().strftime("%Y%m%d")
                #self.cal_end_date = '20170804'
                sql = " SELECT * " \
                      " FROM aif_calculator_status " \
                      " WHERE name = '%s'" % (self.__class__.__name__)
                calculator_status = caiiasdata.getDataBySQL('index', sql)
                self.cal_end_date = calculator_status.trans_date[0]

    def execute(self, **args):
        start_date = args.get('start_date')
        end_date = args.get('end_date')
        is_update_status = args.get('is_update_status', True)

        if is_update_status in (True, '1'):
            self.updateStatus(status=self.STATUS_RUNNING)

        #获取计算的开始日期
        calculation_start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # init calc data
        self.init_data(start_date=start_date, end_date=end_date)

        common.logger.info(
            'try to calculate table %s for start_date %s end_date %s',
                self.table_name, self.cal_start_date, self.cal_end_date
            )
        try:
            # create table
            self.create_table()

            common.logger.info(
                'try to init calc data table %s for start_date %s end_date %s',
                self.table_name, self.cal_start_date, self.cal_end_date
            )

            # load data
            common.logger.info(
            	'try to load data table %s for start_date %s end_date %s',
                	self.table_name, self.cal_start_date, self.cal_end_date
            	)
            self.org_data = self.loadData()
            print self.org_data
            #calculate
            common.logger.info(
            	'try to calculate table %s for start_date %s end_date %s',
                	self.table_name, self.cal_start_date, self.cal_end_date
            	)
            self.result_data = self.calculate()
            print self.result_data
            #self.result_data.to_csv('result_20170803.csv')
            '''
            pool = multiprocessing.Pool()
            n = pool._processes
            common.logger.info(
            	'initialized a process pool of size %d',
                n
            )
            for i in range(n):
                pool.apply_async(self.parallel_calculate, (n, 1))
                self.result_data = self.parallel_calculate(n, i)
            print self.result_data
            '''
            #dump data
            common.logger.info(
            	'try to dump data table %s for start_date %s end_date %s',
                	self.table_name, self.cal_start_date, self.cal_end_date
            	)
            self.dumpData()
        except Exception as e:
            common.logger.exception(
                'failed to calculate table[%s] for start_date[%s] end_date[%s] e[%s]',
                self.table_name, self.cal_start_date, self.cal_end_date, e
            )
            caiiasdata.logger("E",self.__class__.__name__,'failed to calculate table[%s] for start_date[%s] end_date[%s] e[%s]'% (self.table_name, self.cal_start_date, self.cal_end_date, e),calculation_start_time, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            if is_update_status in (True, '1'):
                self.updateStatus(status=self.STATUS_FAILED)
            return self.calculation_failed()

        common.logger.info(
            'finish calculate table %s for start_date %s end_date %s',
                self.table_name, self.cal_start_date, self.cal_end_date
            )

        caiiasdata.logger("S", self.__class__.__name__, 'finish calculate table %s for start_date %s end_date %s' % (self.table_name, self.cal_start_date, self.cal_end_date), calculation_start_time , datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        if is_update_status in (True, '1'):
            self.updateStatus(status=self.STATUS_SUCCESS)
        return self.calculation_ok()

    def init_data(self, start_date, end_date):
        #如果输入执行开始日期，则以输入的为准
        if start_date not in (None, '', '0'):
            self.cal_start_date = start_date
        #如果输入执行终止日期，则以输入的为准
        if end_date not in (None, '', '0'):
            self.cal_end_date = end_date

        if (start_date not in (None, '', '0')) or (end_date not in (None, '', '0')):
            self.__init__()    #
            self.delete_old_data()

    def delete_old_data(self):
        sql = "DELETE FROM %s " \
              " WHERE date >= '%s' " \
              " AND date <= '%s'" % (self.table_name, self.cal_start_date, self.cal_end_date)
        caiiasdata.deleteData('index', sql)

    def calculate(self):
        # 生成工作日序列
        daterng = pd.bdate_range(self.cal_start_date, self.cal_end_date)
        print "daterng:%s"%daterng
        columns = list()
        for c in self.table_columns:
            columns.append(c.name)

        tmp_data = pd.DataFrame(columns=columns)

        for date in daterng:
            result_one_day = self.calculate_one_day(data=self.org_data, today=date.date())
            tmp_data = tmp_data.append(result_one_day, ignore_index=True)

        return tmp_data

    def calculation_ok(self, message='OK'):
        return self.status('0000', message)

    def calculation_failed(self, message='Failed'):
        return self.status('1001', message)

    def status(self, code, message):
        return {
            'errcode': code,
            'errmsg': message
        }

    def __get_fund_start_date(self, code):
        sql_start_info = " SELECT F_INFO_SETUPDATE " \
                         " FROM wd_chinamutualfunddescription" \
                         " WHERE F_INFO_WINDCODE = '%s' " % (code)
        fund_info = caiiasdata.getDataBySQL('orig', sql_start_info)
        return fund_info['F_INFO_SETUPDATE'][0]

    def create_table(self):
        if caiiasdata.isTableExist('index', self.table_name) == False:
            caiiasdata.createTable('index', self.table_name, self.table_columns)

    def get_periods(self, table_columns,today, fund_start_date):
        periods = dict()
        pattern_p = re.compile('.*_[0-9][ymdw]')     #y - 年 m - 月 d - 日 w - 周
        pattern_np = re.compile('.*_[n][0-9|n][ymd]')
        value = list()
        for c in table_columns:
            if c.name[-3:] == 's2n':
                value = (fund_start_date, today)
            elif pattern_p.match(c.name):
                if c.name[-1:] == 'y':
                    value = (months_ago(today, 12*int(c.name[-2:-1])), today)
                elif c.name[-1:] == 'm':
                    value = (months_ago(today, int(c.name[-2:-1])), today)
                elif c.name[-1:] == 'd':
                    value = (days_ago(today, int(c.name[-2:-1])), today)
                elif c.name[-1:] == 'w':
                    value = (days_ago(today, 7*int(c.name[-2:-1])), today)
            elif pattern_np.match(c.name):
                if c.name[-1:] == 'y':
                    if c.name[-2:-1] == 'n':
                        value = (date(today.year, 1, 1), today)
                    else:
                        value = (date(today.year - int(c.name[-2:-1]), 1, 1), date(today.year - int(c.name[-2:-1]), 12, 31))
            if value:
                periods[c.name] = value
        return periods

    def get_start_date(self):
        sql = "select max(date) max_date from %s " %(self.table_name)
        try:
            max_date = caiiasdata.getDataBySQL('index', sql)
            if max_date.empty or max_date['max_date'][0] is None:
                return self.DEFAULT_CAL_START_DATE
            else:
                return max_date['max_date'][0]
        except Exception as e:
            return self.DEFAULT_CAL_START_DATE

    def dumpData(self):
        try:
            caiiasdata.writeData('index', self.table_name, self.result_data, append=True)
        except Exception as e:
            sql = "DELETE FROM %s "\
                    " WHERE date >= '%s' "\
                      " AND date <= '%s'" % (self.table_name, self.cal_start_date, self.cal_end_date)
            caiiasdata.deleteData('index', sql)
            caiiasdata.writeData('index', self.table_name, self.result_data, append=True)

    def loadData(self):
        data = dict()
        for table in self.org_table_list:
            database, sql = self.org_table_list[table]
            info = caiiasdata.getDataBySQL(database, sql)
            data[table] = info
        return data

    def updateStatus(self, status):
        sql = " SELECT * " \
                  " FROM aif_calculator_status " \
              " WHERE name = '%s'" % (self.__class__.__name__)
        calculator_status = caiiasdata.getDataBySQL('index', sql)

        if (status is self.STATUS_RUNNING) or (status is self.STATUS_FAILED):
            sql = " UPDATE aif_calculator_status " \
                     " SET status = '%d' " \
                  " WHERE name = '%s' "  %(status, self.__class__.__name__)
            caiiasdata.updateData('index', sql)
        else:
            calculator_status.finish_num[0] = calculator_status.finish_num[0] + 1
            if calculator_status.max_finish_num[0] > calculator_status.finish_num[0] :
                sql = " UPDATE aif_calculator_status " \
                      " SET status = '%d', " \
                          " finish_num = %d"\
                      " WHERE name = '%s'" % (status, calculator_status.finish_num[0], self.__class__.__name__)
            else:
                next_day = days_after(datetime.datetime.strptime(self.cal_end_date, '%Y%m%d'), 1)
                sql = " UPDATE aif_calculator_status " \
                      " SET status = '%d', " \
                          " finish_num = 0, "\
                          " trans_date = '%s' "\
                      " WHERE name = '%s'" % (status, next_day, self.__class__.__name__)
            caiiasdata.updateData('index', sql)

    def calculate_one_day(self, data, code, today):
        raise NotImplementedError

