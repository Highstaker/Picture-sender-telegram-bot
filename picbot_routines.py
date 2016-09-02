from random import choice
from os import path
from time import sleep

from bot_routines import BotRoutines, BadFileIDError
from database_handler import DatabaseHandler, DatabaseError
from utils import FolderSearch
from textual_data import METADATA_FILENAME
from button_handler import getMainMenu

from settings_reader import SettingsReader
from logging_handler import LoggingHandler
log = LoggingHandler(__name__)
sr = SettingsReader()

PIC_FILE_EXTENSIONS = ("jpg", "jpeg", "gif", "png", "tif", "bmp",)


class PicBotRoutines(BotRoutines):
	def __init__(self, token, database_handler):
		self.database_handler = database_handler

		self.pic_folder = sr["pic_folder"]

		super(PicBotRoutines, self).__init__(token)

	def sendMessageCommandMethod(self, bot, update, text, key_markup=None, *args, **kwargs):
		chat_id = update.message.chat_id
		if key_markup is None:
			key_markup = getMainMenu(self.database_handler.getSubscribed(chat_id))

		self.sendMessage(chat_id, text, key_markup=key_markup, *args, **kwargs)

	def sendLocalRandomPic(self, chat_id):
		"""
		Sends a random picture from a local filesystem. Attaches caption from the folder
		:return:
		"""

		# get list of files from local filesystem
		files = FolderSearch.getFilepathsInclSubfolders(self.pic_folder, allowed_extensions=PIC_FILE_EXTENSIONS)
		# pick a file at random
		random_file = choice(files)

		# if file's cache is present in the database
		cache = self.database_handler.getFileCache(random_file)
		if cache:
			# send cached file by Telegram file ID
			log.debug("sending cached", random_file) #debug
			data = cache
		else:
			log.debug("sending file", random_file) #debug
			data = random_file
			# add the file to database
			self.database_handler.addFile(random_file)
			cache = None

		try:
			metadata_filename = path.join(path.dirname(random_file), METADATA_FILENAME)
			with open(metadata_filename, 'r') as metafile:
				metadata = metafile.read()
		except FileNotFoundError:
			metadata = ""

		try:
			msg = super(PicBotRoutines, self).sendPhoto(chat_id, data, caption=metadata,)
		except BadFileIDError:
			# The ID is broken
			msg = super(PicBotRoutines, self).sendPhoto(chat_id, random_file, caption=metadata,)
			cache = None

		file_id = super(PicBotRoutines, self).getPhotoFileID(msg)

		# update the file ID
		if cache is None:
			# if a cache should be updated, I have set it to `None` above
			self.database_handler.updateCache(random_file, file_id)


if __name__ == '__main__':
	# TESTS
	with open(path.join("tokens", "testbot")) as f:
		parse = f.read().split("\n")
	TOKEN = parse[0].split("#")[0].strip(" \n\r\t")  # your bot token
	CHAT_ID = int(parse[1].split("#")[0])  # your chat_id in your test bot

	# Test pseudo database handler
	class PseudoDatabaseHandler(object):
		"""docstring for PseudoDatabaseHandler"""
		def __init__(self):
			super(PseudoDatabaseHandler, self).__init__()
			self.db = dict()

		def addFile(self, file_path):
			"""
			Add file to DB, if it is not present.
			:param file_path:
			:return: Returns True if there was no file and addition took place. False otherwise
			"""
			try:
				# noinspection PyStatementEffect
				self.db[file_path]
				added = False
			except KeyError:
				self.db[file_path] = {'file_id': None}
				added = True

			return added

		def updateCache(self, file_path, file_id):
			self.db[file_path] = {'file_id': file_id}

		def getFileCache(self, file_path):
			try:
				result = self.db[file_path]['file_id']
			except KeyError:
				result = None

			return result


	# dbh = PseudoDatabaseHandler()
	dbh = DatabaseHandler()
	routines = PicBotRoutines(TOKEN, dbh)

	##############
	# ACTUAL TESTS
	##############

	####################
	# sendLocalRandomPic
	for i in range(10):
		routines.sendLocalRandomPic(CHAT_ID)
		sleep(1)

	# break caches
	for i in dbh.getFileList():
		dbh.updateCache(i, "AgADAgADDq8xG-wJfgrdQ52w0GAAAAclcQ0ABKabtVnUAX_Q-YcBAAEC")
		# dbh.db[i]['file_id'] = "AgADAgADDq8xG-wJfgrdQ52w0GAAAAclcQ0ABKabtVnUAX_Q-YcBAAEC" #for pseudo

	routines.sendLocalRandomPic(CHAT_ID)
