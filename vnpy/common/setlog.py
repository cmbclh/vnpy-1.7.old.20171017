##-*-coding: utf-8;-*-##
import logging
import time
import sys
import os

def setup_logging():
    logger=logging.getLogger()
    logger.setLevel(logging.INFO)
    filename='%s/logfiles/log_%s.log' % (os.path.abspath(os.path.join(os.path.dirname(__file__),'..')),
                                            time.strftime('%Y%m%d',time.localtime(time.time())))
    formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d]-%(levelname)s: %(message)s')
    fn = logging.FileHandler(filename)
    fn.setLevel(logging.INFO)
    fn.setFormatter(formatter)
    logger.addHandler(fn)
