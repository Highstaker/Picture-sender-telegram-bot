#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

from sys import version_info

def check_version(v):
	"""
	Checks if installed version of Python matches or is newer than the one required by the program. If not, quits.
	:param v: The version of Python required by software
	:return:
	"""
	if v >= version_info:
		print("""Sorry, your version of Python is too old!
You have installed in your system: {1}.
Needed by the software: {0}""".format(".".join(map(str, v)), ".".join(map(str,version_info[:len(v)]))))
		quit()

# a quick test
if __name__ == '__main__':
	required_version = (3, 5, 0)
	check_version(required_version)
	print("Version sufficient!")