#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
import os
import sqlite3
from os import path

from textual_data import DATABASES_FOLDER_NAME
from utils import SQLiteUtils
getSQLiteType = SQLiteUtils.getSQLiteType

# The folder containing the script itself
SCRIPT_FOLDER = path.dirname(path.realpath(__file__))

TABLE_NAME = "UserParams"


# noinspection SqlNoDataSourceInspection
class UserParams(object):
	"""docstring for UserParams"""
	def __init__(self, filename, initial=None):
		"""

		:param filename: name of database file without extension
		:param initial: a dictionary of initial parameters. Used to initialize the table
		:return:
		"""
		super(UserParams, self).__init__()
		os.makedirs(path.join(SCRIPT_FOLDER, DATABASES_FOLDER_NAME),exist_ok=True)
		self.filename = path.join(SCRIPT_FOLDER, DATABASES_FOLDER_NAME, filename + ".db")

		# if database already exists, append new columns to it, if any
		if initial:
			if path.isfile(self.filename):
				for i in initial.keys():
					self._addColumn(i, initial[i])
			else:
				#database doesn't exist, create it
				self.createTable(initial)



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

	def createTable(self, data):
		"""
		Creates the table with columns specified in `data`
		:param data: a dictionary with parametes to initialize the table.
		Keys become column names, values have their type read and used as column type
		:return:
		"""
		command = "CREATE TABLE {0}(chat_id INTEGER PRIMARY KEY ".format(TABLE_NAME)

		for i in data.keys():
			command += "," + i + " "
			command += getSQLiteType(data[i])

		command += ");"

		self._run_command(command)

	def initializeUser(self, chat_id, data):
		"""
		Adds a new user to table, if it doesn't exist
		:param chat_id: id of a user. added as the first column
		:param data: a dictionary of values to set for a user
		:return:
		"""
		command = "INSERT INTO {0}(chat_id,".format(TABLE_NAME)
		command += ",".join([str(i) for i in data.keys()])
		command += ") VALUES (" + str(chat_id) + ","
		command += ",".join(["'{0}'".format(str(i)) if isinstance(i,str) else str(i) for i in data.values()])
		command += ");"

		try:
			self._run_command(command)
		except sqlite3.IntegrityError:
			pass

	def getEntry(self, chat_id, param):
		"""
		Returns the entry from database
		:param chat_id: a user id for whom to get the entry
		:param param: a parameter to get
		:return: the parameter value
		"""
		command = "SELECT " + param + " FROM {0} WHERE chat_id=".format(TABLE_NAME) + str(chat_id) + ";"
		data = self._run_command(command)
		return data[0][0]

	def setEntry(self, chat_id, param, value):
		"""
		Sets a database entry to a given value
		:param chat_id: a user id for whom to set the entry
		:param param: the parameter to set
		:param value: the new value of parameter
		:return:
		"""
		command = "UPDATE " + TABLE_NAME + " SET " + str(param) + "=" \
				+ ( ("'"+str(value)+"'") if isinstance(value, str) else str(value) )  \
				+ " WHERE chat_id=" + str(chat_id) + ";"
		self._run_command(command)

	def getAllEntries(self, fields=()):
		"""
		Returns all entries with provided fields
		:param fields: a list of fields to return
		:return:
		"""
		data = None
		if fields:
			command = "SELECT {0} FROM {1}".format(",".join(fields),TABLE_NAME)
			data = self._run_command(command)

		return data


	def _run_command(self, command):
		"""
		Runs a given command and returns the output.
		:param command:
		:return:
		"""
		conn = sqlite3.connect(self.filename)
		cursor = conn.execute(command)
		data =[i for i in cursor]
		conn.commit()
		conn.close()

		return data

#tests
if __name__ == '__main__':
	initial = {"lang": "EN",  # bot's langauge
							"input_mode": 0,
							 "comment": ""
							}
	U = UserParams(filename='test001', initial=initial)
	U.initializeUser(123, {"lang": "RU", "input_mode": 1, "comment": "LOL!"})
	U.initializeUser(123, {"lang": "EN", "input_mode": 3, "comment": "NO LOL!"})
	U.initializeUser(124, {"lang": "EN"})
	U.getEntry(123, "comment")
	U.getEntry(123, "input_mode")
	U.getEntry(124, "comment")
	initial["username"] = "Durak"

	U = UserParams(filename='test001', initial=initial)
	U.initializeUser(125, {"lang": "EN", "username": "idiot"})
	U.setEntry(125,"comment","BWHAHAHA")
	U.setEntry(124,"input_mode",2)
	U.setEntry(125,"input_mode",0)
	print(U.getAllEntries(fields=["input_mode","chat_id","lang"]))