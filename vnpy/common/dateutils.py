import calendar
import datetime
import time


def months_ago(today, n):
    k = today.month - 1 - n

    y = k / 12 + today.year
    m = k % 12 + 1
    d = min(today.day, calendar.monthrange(y, m)[1])

    return datetime.date(y, m , d)

def months_after(today, n):
    k = today.month + 1 + n

    y = k / 12 + today.year
    m = k % 12 + 1
    d = min(today.day, calendar.monthrange(y, m)[1])

    return datetime.date(y, m , d)

def days_ago(today, n):
    return today - datetime.timedelta(days=n)

def days_after(today, n):
    d = today  +  datetime.timedelta(days=n)
    return d.strftime('%Y%m%d')

def strtodate(str):
    t = time.strptime(str,'%Y-%m-%d')
    return t


def initStartTime(currentDate):
    def last_months(sourceDate, months):
        d = months_ago(sourceDate, months)
        return d.strftime('%Y%m%d')

    space = '-'
    year, month, day = currentDate.split(space)
    currentDate=datetime.datetime(int(year),int(month),int(day))
    threeYearAgo = last_months(currentDate,36)
    oneMonthAgo=last_months(currentDate,1)
    oneQuarterAgo=last_months(currentDate,3)
    oneDayAgo=(currentDate-datetime.timedelta(days=1)).strftime('%Y%m%d')
    return threeYearAgo,oneQuarterAgo,oneMonthAgo,oneDayAgo


def current_timestamp():
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
