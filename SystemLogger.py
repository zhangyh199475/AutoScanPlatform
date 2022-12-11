'''
Author: zsh zsh1282984748@163.com
Date: 2022-12-11 10:58:12
LastEditors: zsh zsh1282984748@163.com
LastEditTime: 2022-12-11 13:47:35
FilePath: \ArmScan\SystemLogger.py
Description: 系统日志包
'''
#coding:utf-8

import logging, logging.handlers
from concurrent_log_handler import ConcurrentRotatingFileHandler
import sys

log_format = "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
system_format = logging.Formatter(fmt=log_format)

def logger_init(logger_name="", myfilename = "default.log"): 
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # 检查并添加句柄
    if not logger.handlers: 
        logger.addHandler(streamhandler_init(system_format))
        logger.addHandler(filehandler_init(system_format, myfilename))

    return logger

# 文件输出句柄
def filehandler_init(myformatter, myfilename="default.log"): 
    # # 通过时间自动备份的句柄（更新，由于线程安全性，在flask下会锁死文件。。。不能写入）
    # file_handler = logging.handlers.TimedRotatingFileHandler(myfilename, when="S", interval=10, backupCount=3) # 每天备份一次，存30天的
    # 通过大小自动备份的句柄，具有线程安全性
    file_handler = ConcurrentRotatingFileHandler(myfilename, encoding='utf-8', maxBytes=1024 * 1024, backupCount=30) # 每1M备份一次，备份最多30份
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(myformatter)
    return file_handler

def streamhandler_init(myformatter):
    # 向标准输出的句柄
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(myformatter)
    return stream_handler

if __name__ == "__main__": 
    test_logger = logger_init()
    test_logger.info('test info')
    iter = 0
    while(1): 
        import time
        test_logger.info("loop info: {}".format(iter))
        iter += 1
        time.sleep(3)
    pass