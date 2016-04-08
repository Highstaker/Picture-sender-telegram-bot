#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
#TODO: make a singleton
#TODO: make an object with switchable level
import logging


class LoggingHandler:
	def __init__(self):
		logging.basicConfig(format = u'[%(asctime)s] %(filename)s[LINE:%(lineno)d]# %(levelname)-8s  %(message)s',
							level = logging.WARNING)

	# @staticmethod
	# def setConfigLevel(level="warning"):
	# 	if level.lower() == "warning":
	# 		LEVEL = logging.WARNING
	# 	elif level.lower() == "error":
	# 		LEVEL = logging.ERROR
	# 	elif level.lower() == "debug":
	# 		LEVEL = logging.DEBUG
	#
	#

	@classmethod
	def __call__(cls, *args, **kwargs):
		cls.warning(args[0])

	@staticmethod
	def warning(message):
		logging.warning(message)

	@staticmethod
	def error(message):
		logging.error(message)

	@staticmethod
	def debug(message):
		logging.debug(message)

if __name__ == '__main__':
	#Tests
	log = LoggingHandler()
	LoggingHandler.warning("hello")
	LoggingHandler.error("hola")
	log.debug("debug message")
	log('Guten Tag')
