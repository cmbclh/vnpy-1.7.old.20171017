##-*-coding: utf-8;-*-##
import logging
import numpy as np
from datetime import date
from decimal import Decimal

from caiias import dao
from caiias.calculators.operator import Operator
from caiias.dao.tables import AI_MYPORTFOLIOINCOME as PIncome
from caiias.dao.tables import AI_MYPORTFOLIOINDEXS as PIndexes
from caiias.dao.tables import AI_MYPORTFOLIOINFO as PInfo
from caiias.utils import dateutils


logger = logging.getLogger('maxdrawdown')


class MaxDrawdownOperator(Operator):
    def execute(self, **args):
        pid = args.get('pid')
        channel = args.get('channel')
        event_date = self.strp_event_date(args.get('event_date'))
        year = event_date.year

        if channel == self.CHANNEL_TRANS:
            periods = (
                (date(year-2, 1, 1), date(year-2, 12, 31)),
                (date(year-1, 1, 1), date(year-1, 12, 31)),
                (date(year-0, 1, 1), event_date)
            )
        elif channel == self.CHANNEL_BATCH:
            periods = (
                (date(year-0, 1, 1), event_date),
            )
        else:
            ret = self.parameter_error('channel', channel)
            logger.error('%s', ret)
            return ret

        if pid in (None, '', '0'):
            pid_list = list()
            with dao.session() as s:
                rs = s.query(PInfo).all()
                for r in rs:
                    pid_list.append(r.portfolioid)
            logger.info('will run computation for all portfolios')
        else:
            pid_list = [pid]

        logger.info(
            'try to calculate max drawdown for portfolio %s, periods: %s',
            pid_list, periods
        )

        for p in pid_list:
            for sdate,edate in periods:
                logger.info(
                    'try to calculate max drawdown for portfolio %s, between %s and %s',
                    p, sdate, edate
                )
                last_ret = self.calculate(p, sdate, edate)
                logger.info('finished: %s', last_ret)

        return last_ret


    def calculate(self, pid, date_start, date_end):
        av_list = self.load_accumulated_value(pid, date_start, date_end)
        if len(av_list) < 1:
            logger.warn('no income history found')
            return self.status('0004', 'no data series found')

        mdd = self.maxdrawdown(av_list)
        year = date_end.strftime('%Y')

        self.store_index(pid, year, mdd)

        return self.calculation_ok()


    def load_accumulated_value(self, pid, date_start, date_end):
        sdate = date_start.strftime('%Y%m%d')
        edate = date_end.strftime('%Y%m%d')

        av_list = list()
        with dao.session() as s:
            rs = s.query(PIncome).filter_by(
                portfolioid=pid
            ).filter(
                PIncome.transdate.between(sdate, edate)
            ).order_by(
                PIncome.transdate
            ).all()
            for r in rs:
                av = r.accuvalue
                if av is not None:
                    av_list.append(av)

        return av_list


    def store_index(self, pid, year, mdd):
        with dao.session() as s:
            r = s.query(PIndexes).filter_by(
                portfolioid=pid
            ).filter_by(
                indexyear=year
            ).first()
            if r is None:
                r = PIndexes()
                r.portfolioid = pid
                r.indexyear = year

            r.maxdrawdown = mdd
            s.add(r)


    def maxdrawdown(self, it):
        series = np.array([Decimal(v) for v in it])
        drawdown = np.maximum.accumulate(series) - series

        end = np.argmax(drawdown)
        start = np.argmax(series[:end+1])

        v = series[start]
        if v is None or v.is_zero():
            logger.warn('start accumulated value is zero')
            return Decimal(0.0)

        return drawdown[end] / series[start]
