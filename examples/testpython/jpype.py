# encoding: utf-8

#import jpypex
import sys
sys.path.append('../')
#sys.path.append('D:\\tr\\vnpy-master\\vn.trader\\DAO')
sys.path.append('D:/tr/vnpy-1.7/vnpy/common')
#sys.path.append('D:/Program Files/Anaconda2/Lib/site-packages')
sys.path.append('D:/Python27/Lib')
import os
import os.path
import jpype
from jpype import *

#jvmPath = jpype.jvmPath
#print jvmPath
startJVM("D:/Program Files/Java/jdk1.8.0_51/jre/bin/server/jvm.dll", "-ea")
java.lang.System.out.println("hello World")
shutdownJVM()