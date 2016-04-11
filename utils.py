#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
from os import path, walk
from time import sleep
from calendar import timegm
import requests
import json
import datetime

from traceback_printer import full_traceback
from logging_handler import LoggingHandler
logging = LoggingHandler


class DictUtils:
	@staticmethod
	def replaceKey(dic, oldkey, newkey):
		try:
			dic[newkey] = dic.pop(oldkey)
		except KeyError:
			raise KeyError("Could not replace key {0}. It was not found!".format(oldkey))

	@staticmethod
	def dictGetCaseInsensitive(dic, key):
		result = None
		try:
			# maybe it already exists as-is
			result = dic[key]
		except KeyError:
			error_message = "The key was not found, even case-insensitively"
			if isinstance(key, str):
				# try to find case-insensitively
				upper_key = key.upper()
				for i in dic:
					if i.upper() == upper_key:
						result = dic[i]
						break
				else:
					raise KeyError(error_message)
			else:
				raise KeyError(error_message)

		return result

class FolderSearch:

	@staticmethod
	def getFilepathsInclSubfolders(FOLDER, allowed_extensions=None):
		"""
		Returns a list of full paths to all files in a folder and subfolders. Follows links!
		param allowed_extensions: if provided, adds only files with specified extensions
		"""
		myFolder = FOLDER
		fileSet = set()

		for root, dirs, files in walk(myFolder,followlinks=True):
			for fileName in files:
				if not allowed_extensions or path.splitext(fileName)[1].replace('.','').lower() in [i.lower() for i in allowed_extensions]:
					fileSet.add( path.join( root, fileName ))
		return list(fileSet)


class DropboxFolderSearch:

	@staticmethod
	def getFilepathsInclSubfoldersDropboxPublic(LINK, DROPBOX_APP_KEY, DROPBOX_SECRET_KEY, unixify_mod_time=True):
		'''
		Returns a list of full paths to all files in a public folder (provided with a link) and subfolders in Dropbox
		:param unixify_mod_time: if True, file modification time is returned as Unix time integer.
		Else, the format is 'Wed, 07 Oct 2015 13:22:49 +0000'
		:param DROPBOX_APP_KEY:
		:param DROPBOX_SECRET_KEY:
		:param LINK: link to a public folder in Dropbox
		:return: (filepath,modification time) tuple. Modification time in format 'Wed, 07 Oct 2015 13:22:49 +0000'
		'''

		def readDir(LINK, DIR):

			def unixify_date(d):
				MONTHS = {"Jan": "01",
						  "Feb": "02",
						  "Mar": "03",
						  "Apr": "04",
						  "May": "05",
						  "Jun": "06",
						  "Jul": "07",
						  "Aug": "08",
						  "Sep": "09",
						  "Oct": "10",
						  "Nov": "11",
						  "Dec": "12"
						  }
				d = d.split(",")[1].strip(" ")
				for i in MONTHS.keys():
					d = d.replace(i, MONTHS[i])

				result = timegm(datetime.datetime.strptime(d, "%d %m %Y %H:%M:%S %z").timetuple())
				# print(result)#debug
				return result

			#Set a loop to retry connection if it is refused
			result = []
			while True:
				try:
					req=requests.post('https://api.dropbox.com/1/metadata/link',
									  data=dict( link=LINK, client_id=DROPBOX_APP_KEY,
												 client_secret=DROPBOX_SECRET_KEY, path=DIR) )

					if not req.ok:
						print("Retrying! req.status_code", req.status_code)#debug
						continue

					for i in json.loads(req.content.decode())['contents']:
						if i['is_dir']:
							logging.warning("Reading directory: " + str(i['path']))
							result += readDir(LINK,i['path'])
						else:
							#a file, add to list
							if unixify_mod_time:
								result += [(i['path'], unixify_date(i['modified']),)]
							else:
								result += [(i['path'], i['modified'],)]

					break
				except Exception as e:
					print("Dropbox error:" + full_traceback())
					sleep(60)#wait a bit before retrying
					pass

			return result

		filelist = readDir(LINK,"/")

		return filelist


class SQLiteUtils:

	@staticmethod
	def getSQLiteType(param):
		"""
		Returns the SQLite type of a given parameter
		:param param: a parameter a type of which should be returned
		:return: a string representing an SQLite type
		"""
		if isinstance(param, str):
			result = "TEXT"
		elif isinstance(param, int):
			result = "INTEGER"
		elif isinstance(param,float):
			result = "DECIMAL"
		else:
			result = "BLOB"

		return result

	@staticmethod
	def escapeText(text):
		return text.replace("'", "''")

class FileUtils:

	@staticmethod
	def getModificationTimeUnix(filepath):
		"""
		Returns the modification time of a file as Unix time
		:param filepath:
		:return:
		"""
		try:
			result = int(path.getmtime(filepath))
		except FileNotFoundError:
			result = 0

		return result