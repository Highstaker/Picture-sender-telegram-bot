#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
import sys, traceback

def full_traceback():
	"""
	Returns a full traceback to an exception
	:return:
	"""
	exc_type, exc_value, exc_traceback = sys.exc_info()
	a = traceback.format_exception(exc_type, exc_value, exc_traceback)
	a = "".join(a)
	return a

if __name__ == '__main__':
	# A quick test
	def a():
		raise KeyError

	def b():
		return a()

	try:
		b()
	except KeyError:
		print(full_traceback())