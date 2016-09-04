from random import choice, sample
from os import path
from time import sleep
from threading import Thread

from bot_routines import BotRoutines, BadFileIDError
from database_handler import DatabaseHandler, DatabaseError
from utils import FolderSearch, FileUtils
from textual_data import METADATA_FILENAME
from button_handler import getMainMenu
from parameters import PIC_FILE_EXTENSIONS

from settings_reader import SettingsReader
from logging_handler import LoggingHandler
log = LoggingHandler(__name__, max_level="DEBUG")
sr = SettingsReader()

class PicBotRoutines(BotRoutines):
	def __init__(self, token, database_handler, dropbox_handler=None):
		self.database_handler = database_handler

		self.pic_folder = sr["pic_folder"]

		self.dropbox_handler = dropbox_handler

		# contains pic-sending threads for each user. Only one hsould be run per user at a time
		self.db_pic_sender_threads = dict()

		super(PicBotRoutines, self).__init__(token)

	def sendMessageCommandMethod(self, bot, update, text, key_markup=None, *args, **kwargs):
		chat_id = update.message.chat_id
		if key_markup is None:
			key_markup = getMainMenu(self.database_handler.getSubscribed(chat_id))

		self.sendMessage(chat_id, text, key_markup=key_markup, *args, **kwargs)

	def getLocalFiles(self):
		"""

		:return: a set of image file paths
		"""
		return FolderSearch.getFilepathsInclSubfolders(self.pic_folder, allowed_extensions=PIC_FILE_EXTENSIONS)

	def sendLocalRandomPic(self, chat_id):
		"""
		Sends a random picture from a local filesystem. Attaches caption from the folder
		:return:
		"""

		# get list of files from local filesystem
		files = self.getLocalFiles()
		if not files:
			self.sendMessage(chat_id, "Sorry, no images available!")
			return

		# pick a file at random. `files` is a set, `random.choice` won't work
		random_file = sample(files, 1)[0]
		log.info("random_file", random_file)
		mod_time = FileUtils.getModificationTimeUnix(random_file)

		cache = self.database_handler.getFileCache(random_file)
		db_mod_time = self.database_handler.getFileModtime(random_file)
		# log.debug("cache", cache)  # debug
		# log.debug("db_mod_time", db_mod_time)  # debug

		# if file's cache is present in the database
		if cache and db_mod_time >= mod_time:
			# send cached file by Telegram file ID
			log.debug("sending cached", random_file) #debug
			data = cache
		else:
			log.debug("sending file", random_file) #debug
			data = random_file
			# add the file to database
			self.database_handler.addFile(random_file, mod_time=mod_time)
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
			self.database_handler.updateModtime(random_file, mod_time)
			self.database_handler.updateCache(random_file, file_id)

	def sendDropboxRandomPic(self, chat_id):
		if not chat_id in self.db_pic_sender_threads or not self.db_pic_sender_threads[chat_id].is_alive():
			t = Thread(target=self._sendDropboxRandomPicThread, args=(chat_id,))
			self.db_pic_sender_threads[chat_id] = t
			t.start()
		else:
			self.sendMessage(chat_id, "I'm still sending you a picture. Please wait!")

	def _sendDropboxRandomPicThread(self, chat_id):
		"""
		Sends a random picture from Dropbox storage. Attaches caption from the folder
		:param chat_id:
		:return:
		"""

		# get list of files from database
		files = FileUtils.filterByExtension(self.database_handler.getFileList(), PIC_FILE_EXTENSIONS)
		if not files:
			self.sendMessage(chat_id, "Sorry, no images available!")
			return

		# pick a file at random.
		random_file = choice(files)
		log.info("random_file", random_file)

		cache = self.database_handler.getFileCache(random_file)
		# db_mod_time = self.database_handler.getFileModtime(random_file)

		if cache:
			# send cached file by Telegram file ID
			log.debug("sending cached", random_file) #debug
			data = cache
		else:
			log.debug("Not cached, getting a file from Dropbox!")  # debug
			data = self.dropbox_handler.getDropboxFile(random_file)
			if not data:
				# if not data, the file is probably gone, retry the whole routine
				self._sendDropboxRandomPicThread(chat_id)
				return

		metadata = self.database_handler.getMetadataForFile(random_file)

		try:
			msg = super(PicBotRoutines, self).sendPhoto(chat_id, data, caption=metadata,)
		except BadFileIDError:
			# The ID is broken, resend file
			data = self.dropbox_handler.getDropboxFile(random_file)
			if not data:
				# if not data, the file is probably gone, retry the whole routine
				self._sendDropboxRandomPicThread(chat_id)
				return
			msg = super(PicBotRoutines, self).sendPhoto(chat_id, data, caption=metadata,)
			cache = None

		file_id = super(PicBotRoutines, self).getPhotoFileID(msg)

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
