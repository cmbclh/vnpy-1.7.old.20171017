##-*-coding: utf-8;-*-##
import logging
import time
import sys
import os

'''
日志打印接口，import commong后，使用common.logger对象执行相应级别的日志打印操作。
    import common
    common.logger.debug("this is debug")
    common.logger.info("this is info")
    common.logger.warning("this is warning")
    common.logger.error("this is error")
    common.logger.critical("this is critical")
以上只有info、warning、error、critical四个级别的日志会被打印到logfiles下。
'''

logging.basicConfig(level=logging.INFO,
                    filename='%s/logfiles/log_%s.log' % (os.path.abspath(os.path.join(os.path.dirname(__file__),'..')),
                                                         time.strftime('%Y%m%d',time.localtime(time.time()))),
                    filemode='a',
                    format='%(asctime)s %(filename)s[line:%(lineno)d]-%(levelname)s: %(message)s')
logger=logging.getLogger()