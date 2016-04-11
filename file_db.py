#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
import os
import sqlite3

import utils
from os import path
from utils import SQLiteUtils
getSQLiteType = SQLiteUtils.getSQLiteType
from threading import Lock

from textual_data import DATABASES_FOLDER_NAME, METADATA_FILENAME

# The folder containing the script itself
SCRIPT_FOLDER = path.dirname(path.realpath(__file__))

TABLE_NAME = "files"


# noinspection SqlNoDataSourceInspection,SqlDialectInspection
class FileDB(object):
	def __init__(self, filename):
		"""

		:param filename: name of database file without extension
		:return:
		"""
		super(FileDB, self).__init__()
		os.makedirs(path.join(SCRIPT_FOLDER, DATABASES_FOLDER_NAME),exist_ok=True)
		self.filename = path.join(SCRIPT_FOLDER, DATABASES_FOLDER_NAME, filename + ".db")

		# A lock for thread safety
		self.lock = Lock()

		# Type 0 - file, 1 - metadata for folder
		initial={"type":0, 'meta':'str', 'path':'str', 'mod_time':0, 'file_id':"str"}

		# if database already exists, append new columns to it, if any
		if initial:
			if path.isfile(self.filename):
				for i in initial.keys():
					self._addColumn(i, initial[i])
			else:
				#database doesn't exist, create it
				self.createTable(initial)

	def getDBFilename(self):
		"""
		Returns the file path to database file
		:return:
		"""
		return self.filename

	def createTable(self, data):
		"""
		Creates the table with columns specified in `data`
		:param data: a dictionary with parametes to initialize the table.
		Keys become column names, values have their type read and used as column type
		:return:
		"""
		command = "CREATE TABLE {0}(ID INTEGER PRIMARY KEY ".format(TABLE_NAME)

		for i in data:
			command += "," + i + " "
			command += getSQLiteType(data[i])

		command += ");"

		self._run_command(command)

	def _addColumn(self, column, init_data):
		"""
		Adds a column to the table, if it doesn't exist
		:param column: name of the new column
		:param init_data: data to be put in that column. Used to determine the type
		:return:
		"""
		command = "ALTER TABLE " + TABLE_NAME + " ADD COLUMN " + str(column) + " " + getSQLiteType(init_data)
		try:
			self._run_command(command)
		except sqlite3.OperationalError:
			print("Column " + str(column) + " already exists!")

	def _run_command(self, command):
		"""
		Runs a given command and returns the output.
		:param command:
		:return:
		"""
		with self.lock:
			conn = sqlite3.connect(self.filename)
			cursor = conn.execute(command)
			data =[i for i in cursor]
			conn.commit()
			conn.close()

		return data

	def getIDbyPath(self, pth):
		"""
		Returns the DB ID by a path field
		:param pth:
		:return:
		"""

		command = "SELECT ID FROM {0} WHERE path='{1}';".format(TABLE_NAME,pth)
		data = self._run_command(command)

		try:
			result = data[0][0]
		except IndexError:
			result = None

		return result

	def fileExists(self, pth):
		"""
		Returns True if a file with a given path is in DB.
		:param pth:
		:return: bool
		"""
		return bool(self.getIDbyPath(pth))

	def addFile(self, pth, mod_time=None):
		"""
		Adds a file with a given path. Doesn't, if the file with given path already exists in DB.
		:param pth:
		:return:
		"""
		if not self.fileExists(pth):
			if not mod_time:
				mod_time = utils.FileUtils.getModificationTimeUnix(pth)

			command = "INSERT INTO {0} (type, path, mod_time) VALUES (0, '{1}', {2});".format(TABLE_NAME, pth, mod_time)

			self._run_command(command)
		else:
			print("addFile: File already exists!")#debug

	def getModTime(self, pth):
		"""
		Gets the modification time of a file in DB
		:param pth:
		:return: integer or None
		"""
		if self.fileExists(pth):
			command = "SELECT mod_time FROM {0} WHERE path='{1}';".format(TABLE_NAME, pth)
			result = self._run_command(command)
			try:
				result = result[0][0]
			except IndexError:
				result = None
		else:
			print("getModTime: File doesn't exist")
			result = None

		return result

	def updateModTime(self, pth, mod_time):
		"""
		Updates the modification time of a file in the DB
		:param pth: file in DB to assign this to
		:param mod_time: new modification time to assign
		:return:
		"""
		if self.fileExists(pth):
			command = "UPDATE {0} SET mod_time={1} WHERE path='{2}';".format(TABLE_NAME, mod_time, pth)
			self._run_command(command)
		else:
			print("updateModTime: file doesn't exist!")

	def addMetafile(self, pth, metadata, mod_time):
		"""
		Adds metadata entry
		:param pth: path to a metadata file
		:param metadata:
		:return:
		"""

		if not self.fileExists(pth):
			command = "INSERT INTO {0} (type, path, meta, mod_time) VALUES (1, '{1}', '{2}', '{3}');".format(TABLE_NAME,
																			pth,
																			utils.SQLiteUtils.escapeText(metadata),
																			mod_time
																			)
			self._run_command(command)
		else:
			print("addMetafile: Meta File already exists!")#debug

	def updateMetadata(self, pth, metadata, mod_time):
		"""
		Updates metadata for a folder
		:param pth: path to a metadata file
		:param metadata: new metadata
		:return:
		"""
		if self.fileExists(pth):
			command = "UPDATE {0} SET meta='{1}', mod_time='{3}' WHERE path='{2}';".format(TABLE_NAME,
																		utils.SQLiteUtils.escapeText(metadata),
																		pth,
																		mod_time)
			self._run_command(command)
		else:
			print("updateMetadata: file doesn't exist!")#debug

	def getMetadata(self, pth):
		"""
		Gets metadata for a file in DB
		:param pth: path to a metadata file
		:return: string
		"""
		if self.fileExists(pth):
			command = "SELECT meta FROM {0} where path='{1}';".format(TABLE_NAME, pth)
			data = self._run_command(command)
			try:
				data = data[0][0]
			except IndexError:
				data = None
		else:
			print("getMetadata: file doesn't exist!")#debug
			data = None

		return data

	def getFileList(self):
		"""
		Returns the list of all files (paths) in DB
		:return: string
		"""
		command = "SELECT path FROM {0};".format(TABLE_NAME)
		data = self._run_command(command)
		try:
			data = [i[0] for i in data]
		except IndexError:
			data = None

		return data

	def getFileListPics(self):
		"""
		Returns the list of all picture files (paths) (type 0) in DB
		:return: string
		"""
		command = "SELECT path FROM {0} WHERE type=0;".format(TABLE_NAME)
		data = self._run_command(command)
		try:
			data = [i[0] for i in data]
		except IndexError:
			data = None

		return data

	def deleteFile(self, pth):
		"""
		Deletes file with a given path from the DB. If it doesn't exist, ignores.
		:param pth:
		:return:
		"""
		command = "DELETE FROM {0} WHERE path='{1}';".format(TABLE_NAME, pth)
		self._run_command(command)

	def updateCacheID(self, pth, cacheID):
		"""
		Updates the file_id field to a given value
		:param pth:
		:param cacheID:
		:return:
		"""
		command = "UPDATE {0} SET file_id='{1}' WHERE path='{2}'".format(TABLE_NAME, cacheID, pth)
		self._run_command(command)

	def getFileCacheID(self, pth):
		"""
		Returns ID of a cached file on Telegram from DB. None if file doesn't exist or has no cached ID.
		:param pth:
		:return:
		"""
		command = "SELECT file_id FROM {0} WHERE path='{1}'".format(TABLE_NAME, pth)
		data = self._run_command(command)

		try:
			data = data[0][0]
		except IndexError:
			data = None

		return data

	def invalidateCached(self, pth):
		"""
		Set cache to NULL in DB for a given file
		:param pth:
		:return:
		"""
		command = "UPDATE {0} SET file_id=NULL WHERE path='{1}'".format(TABLE_NAME, pth)
		self._run_command(command)

	def getCaption(self, pth):
		"""
		Returns a metadata for a given metadata file from DB.
		:param pth: path to a *metadata* file
		:return:
		"""
		command = "SELECT meta FROM {0} WHERE path='{1}';".format(TABLE_NAME,pth)
		data = 	self._run_command(command)

		try:
			data = data[0][0]
		except IndexError:
			data = None

		return data

	def getCaptionPic(self, pth):
		"""
		Returns a metadata for a given picture file From DB.
		Unlike `getCaption`, it gets the folder based on path to pic automatically.
		:param pth: path to a *picture* file
		:return:
		"""
		pth = path.join(path.dirname(pth), METADATA_FILENAME)
		data = self.getCaption(pth)

		return data


if __name__ == '__main__':
	db = FileDB("file_db_test")
	print(db.fileExists("/abc/001.jpg"))#False
	db.addFile("/abc/001.jpg")
	db.addFile("/abc/002.jpg", mod_time=1001)
	db.addFile(path.join(SCRIPT_FOLDER,'tests/test_pics/pic3.jpg'))
	print(db.fileExists("/abc/001.jpg"))#True

	print(db.getModTime("/abc/001.jpg"))#0
	print(db.getModTime("/abc/002.jpg"))#1001
	print(db.getModTime("/abc/003.jpg"))#None
	print(db.getModTime(path.join(SCRIPT_FOLDER,'tests/test_pics/pic3.jpg')))#Big integer

	db.updateModTime("/abc/001.jpg", 42000)
	print(db.getModTime("/abc/001.jpg"))#42000
	print(db.getModTime("/abc/404.jpg"))#None

	db.addMetafile(path.join("/abc/", METADATA_FILENAME), "Nothing\nReally,nothing!", 3333)
	print(db.getMetadata(path.join("/abc/", METADATA_FILENAME)))#Nothing really
	db.updateMetadata(path.join("/abc/", METADATA_FILENAME), "Something\nSomething already!", 9999)
	print(db.getMetadata(path.join("/abc/", METADATA_FILENAME)))#Something already!
	db.addMetafile(path.join("/xyz/", METADATA_FILENAME),
				"""ejeaotun.w"n65wnn.w6wiá9uy4w'w45mn5Øo4bu..ehe\nwgH\tehbae\reaiomb""", 11111)
	print(db.getMetadata(path.join("/xyz/", METADATA_FILENAME)))#gibberish

	print(db.getMetadata(path.join("/ac/", METADATA_FILENAME)))#None

	db.updateCacheID('/abc/001.jpg','AgADAgADzbExGwXC2QezXXRbQpfP3F7JgioABAQl8awcYOsqLrsBAAEC')
	db.updateCacheID('/xxxxx/xxx.jpg','AgADAgADzbExGwXC2QezXXRbQpfP3F7JgioABAQl8awcYOsqLrsBAAEC')#try to set cache to nonexisting file
	print("getFileCacheID /abc/001.jpg", db.getFileCacheID('/abc/001.jpg'))#AgADAgADzbExGwXC2QezXXRbQpfP3F7JgioABAQl8awcYOsqLrsBAAEC
	print("getFileCacheID /abc/002.jpg", db.getFileCacheID('/abc/002.jpg'))#try to get cache of a file that has no cache yet
	print("getFileCacheID /xxxxx/xxx.jpg", db.getFileCacheID('/xxxxx/xxx.jpg'))#try to get cache of nonexisting file
	db.invalidateCached('/xxxxx/xxx.jpg')#invalidate nonexisting file
	db.invalidateCached('/abc/001.jpg')
	print("getFileCacheID /abc/001.jpg", db.getFileCacheID('/abc/001.jpg'))#None

	print(db.getFileList())#lists all files
	db.deleteFile('/abc/001.jpg')
	print(db.getFileList())#lists all files without '/abc/001.jpg
	db.deleteFile('/xxxxx/xxx.jpg')# try deleting non-existing file
	print(db.getFileList())#lists all files without '/abc/001.jpg
	print(db.getFileListPics())#returns only pictures. No metadata files

	# Remove the test DB file
	# os.remove(db.getDBFilename())