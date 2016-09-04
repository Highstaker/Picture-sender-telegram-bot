#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
import logging
from logging.handlers import RotatingFileHandler
from os import path, makedirs

LOGS_DIR = "logs"
DEBUG_FILE_NAME = 'debug.log'
MAX_LOG_SIZE = 10 * 1024 * 1024
BACKUP_FILES_AMOUNT = 3
LOG_FORMAT = u'[%(asctime)s] %(name)s: %(filename)s[LINE:%(lineno)d]# %(levelname)-8s  %(message)s'


# def basicConf():
# 	class Devnull(object):
# 		def write(self, *_, **__): pass
#
# 	fmter = logging.Formatter(LOG_FORMAT)
#
# 	sh = logging.StreamHandler()
# 	sh.setLevel(logging.WARNING)
# 	sh.setFormatter(fmter)
#
# 	fh = RotatingFileHandler(path.join(LOGS_DIR, DEBUG_FILE_NAME),
# 							 maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_FILES_AMOUNT)
# 	fh.setLevel(logging.WARNING)
#
# 	logging.basicConfig(format=LOG_FORMAT,
# 						level=logging.DEBUG,
# 						handlers=(fh,),
# 						# stream=Devnull(),
# 						# filename=path.join(LOGS_DIR, DEBUG_FILE_NAME),
# 						# filemode='a',
# 						)  # passing file handler here, because some libraries use root logger
#
# basicConf()
#
#


class LoggingHandler:
	def __init__(self, logger_name, max_level="WARNING"):
		makedirs(LOGS_DIR, exist_ok=True)

		self.main_logger = logging.getLogger(logger_name)

		self.main_logger.setLevel(logging.DEBUG)

		# create file handler which logs even debug messages
		fh = RotatingFileHandler(path.join(LOGS_DIR, DEBUG_FILE_NAME),
								 maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_FILES_AMOUNT)
		fh.setLevel(logging.DEBUG)
		# create console handler with a higher log level
		ch = logging.StreamHandler()
		ch.setLevel(max_level)
		# create formatter and add it to the handlers
		fmter = logging.Formatter(LOG_FORMAT)
		fh.setFormatter(fmter)
		ch.setFormatter(fmter)
		# add the handlers to the logger
		# self.main_logger.addHandler(fh)
		self.main_logger.addHandler(ch)

		logging.basicConfig(format=LOG_FORMAT,
							level=logging.WARNING,
							handlers=(fh,) + ((ch,) if logger_name != "__main__" else ()),
							# stream=Devnull(),
							# filename=path.join(LOGS_DIR, DEBUG_FILE_NAME),
							# filemode='a',
							)  # passing file handler here, because some libraries use root logger




	def error(self, *args, sep=" "):
		message = sep.join(str(i) for i in args)
		self.main_logger.error(message)
		# logging.error(message)

	def warning(self, *args, sep=" "):
		message = sep.join(str(i) for i in args)
		self.main_logger.warning(message)
		# logging.warning(message)

	def info(self, *args, sep=" "):
		message = sep.join(str(i) for i in args)
		self.main_logger.info(message)
		# logging.info(message)

	def debug(self, *args, sep=" "):
		message = sep.join(str(i) for i in args)
		self.main_logger.debug(message)
		# logging.debug(message)

if __name__ == '__main__':
	# Tests
	log = LoggingHandler(__name__, max_level=logging.INFO)
	log.warning("hello")
	log.error("hola")
	log.info("info message")
	log.debug("debug message")

	logging.warning("logging hello")
	logging.error("logging hola")
	logging.info("logging info message")
	logging.debug("logging debug message")

	weird_logger = logging.getLogger("weird")
	weird_logger.warning("weird_logger hello")
	weird_logger.error("weird_logger hola")
	weird_logger.info("weird_logger info message")
	weird_logger.debug("weird_logger debug message")