from os import path, makedirs
import time as m_time

from generic_db import GenericDatabaseHandler
from textual_data import SCRIPT_FOLDER
from settings_reader import SettingsReader
sr = SettingsReader()

DATABASES_FOLDER_NAME = "databases"
DB_FILENAME = "picbot.db"


def time():
	return int(m_time.time())

class DatabaseError(Exception):
	pass


class DatabaseHandler(GenericDatabaseHandler):
	"""docstring for DatabaseHandler"""

	def __init__(self):
		makedirs(path.join(SCRIPT_FOLDER, DATABASES_FOLDER_NAME), exist_ok=True)
		db_filepath = path.join(SCRIPT_FOLDER, DATABASES_FOLDER_NAME, DB_FILENAME)

		super(DatabaseHandler, self).__init__(db_filepath)

		self._createTables()

	def _createTables(self):
		# table of users
		params = ({'name': 'chat_id', 'type': "INTEGER", "primary_key": True},
				  {'name': 'lang', 'type': "TEXT"},
				  {'name': 'subscribed', 'type': "INTEGER"},  # bool really
				  {'name': 'send_period', 'type': "INTEGER"},
				  {'name': 'last_update_time', 'type': "INTEGER"},
				  )

		self._createTable(table_name="users", params=params)

		# table of files
		params = (
			{'name': 'id', 'type': "INTEGER", "primary_key": True},  # rowid is created automatically, but, whatever
			{'name': 'file_path', 'type': "TEXT", "unique": True},
			{'name': 'file_type', 'type': "INTEGER"},  # 1 is picture, 2 is metadata text
			{'name': 'file_id', 'type': "TEXT"},
			{'name': 'metadata', 'type': "TEXT"},
		)

		self._createTable(table_name="files", params=params)

		# table of collections
		params = (
			{'name': "id", 'type': "INTEGER"},
			{'name': "user_id", 'type': "INTEGER"},
			{'name': "picture_id", 'type': "INTEGER"},
		)

		self._createTable(table_name="collections", params=params)

	def initializeUser(self, chat_id):
		"""

		:param chat_id:
		:return:
		"""
		res = self._addEntry("users", chat_id=chat_id, lang="EN", subscribed="0",
							 send_period=sr['picture_send_period'], last_update_time=time())

		return res

	def getLang(self, chat_id):
		data = self._getEntryEquals("users", "chat_id", chat_id, "lang")
		try:
			data = data[0][0]
		except IndexError:
			data = None

		return data

	def getSubscribed(self, chat_id):
		data = self._getEntryEquals("users", "chat_id", chat_id, "subscribed")
		try:
			data = bool(data[0][0])
		except IndexError:
			data = None

		return data

	def getSendTime(self, chat_id):
		"""
		Returns the UNIX time when a picture should be sent to the user
		:param chat_id:
		:return:
		"""
		data = self._getEntryEquals("users", "chat_id", chat_id, "send_period", "last_update_time")

		try:
			result = data[0][0] + data[0][1]
		except KeyError:
			return None

		return result

	def subscribeUser(self, chat_id):
		self._updateEntriesEqual("users","chat_id", chat_id, subscribed=1)

	def unsubscribeUser(self, chat_id):
		self._updateEntriesEqual("users","chat_id", chat_id, subscribed=0)

	def resetTimer(self, chat_id):
		self._updateEntriesEqual("users","chat_id", chat_id, last_update_time=time())

	def setPeriod(self, chat_id, period):
		self._updateEntriesEqual("users", "chat_id", chat_id, send_period=period)

	def getPeriod(self, chat_id):
		result = self._getEntryEquals("users", "chat_id", chat_id, "send_period")

		try:
			result = result[0][0]
		except IndexError:
			result = None

		return result

	def addFile(self, file_path, metadata=None):
		"""
		Add file to DB, if it is not present.
		:param file_path:
		:return: Returns True if there was no file and addition took place. False otherwise
		"""
		meta = metadata if metadata else ""
		file_type = 2 if metadata else 1

		result = self._addEntry("files", file_path=file_path, metadata=meta, file_type=file_type)
		return result

	def updateCache(self, file_path, file_id):
		"""
		Updates the file_id in database.
		:param file_path:
		:param file_id: ID of a file on Telegram servers
		:return:
		"""

		self._updateEntriesEqual("files", "file_path", file_path, file_id=file_id)

	def getFileCache(self, file_path):
		"""
		Returns the file_id (the ID of a file on Telegram servers) from database.
		:param file_path:
		:return:
		"""
		result = self._getEntryEquals("files", "file_path", file_path, "file_id")
		try:
			result = result[0][0]
		except IndexError:
			result = None

		return result

	def getAllSubscribedUserIDs(self):
		result = self._getEntryEquals("users", "subscribed", 1, "chat_id")

		try:
			result = sum(result, ())  # flatten
		except IndexError:
			result = None

		return result

	def getFileList(self):
		"""

		:return: list of all files in database
		"""
		result = self._getEntryEquals("files", None, None, "file_path")

		try:
			result = sum(result, ())  # flatten
		except IndexError:
			result = None

		return result


if __name__ == '__main__':
	h = DatabaseHandler()
	h.addFile("/tmp/hello.jpg")
	h.addFile("/tmp/metta.txt", metadata="Nöthing really")
	h.updateCache("/tmp/hello.jpg", file_id="blahblahID")
	print(h.getFileCache("/tmp/hello.jpg"))
	print(h.getFileCache("/tmp/metta.txt"))
	print(h.getFileList())

