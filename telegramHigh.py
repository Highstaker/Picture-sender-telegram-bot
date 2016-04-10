#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import io
import telegram
import socket
from os import path, makedirs
from time import sleep
from traceback_printer import full_traceback
import re

#Initialize logging handler
from logging_handler import LoggingHandler
logging = LoggingHandler()

# if a connection is lost and getUpdates takes too long, an error is raised
socket.setdefaulttimeout(30)

############
# PARAMETERS
############


##########
# METHODS
#########


############
# CLASSES###
############


class TelegramHigh:
	"""
	TelegramHigh is a library that helps handling Telegram bots in Python.
	"""

	def __init__(self, token):
		"""

		:param token: Telegram bot token. Can be received from BotFather.
		:return: None
		"""
		super(TelegramHigh, self).__init__()
		# an identifier of the last update object.
		self.LAST_UPDATE_ID = None
		# Initialize bot
		self.bot = telegram.Bot(token)

	@staticmethod
	def isPhoto(update):
		"""
		Returns true if the given message is a Photo.
		:param update: an update object containing a message.
		:return: True or False
		"""
		try:
			return bool(update.message.photo)
		except AttributeError:
			return False

	@staticmethod
	def messageIsPhoto(message):
		"""
		Returns true if the given message is a Photo.
		:param message: an message object
		:return: True or False
		"""
		try:
			return bool(message.photo)
		except AttributeError:
			return False


	@staticmethod
	def isDocument(update):
		"""
		Returns true if the given message is a Document (a File).
		:param update: an update object containing a message.
		:return: True or False
		"""
		try:
			return bool(update.message.document)
		except AttributeError:
			return False

	@staticmethod
	def messageIsDocument(message):
		"""
		Returns true if the given message is a Document (a File).
		:param message: an message object
		:return: True or False
		"""
		try:
			return bool(message.document)
		except AttributeError:
			return False

	@staticmethod
	def escape_markdown(text):
		"""Helper function to escape telegram markup symbols"""
		escape_chars = '\*_`\['
		return re.sub(r'([%s])' % escape_chars, r'\\\1', text)

	@staticmethod
	def breakLongMessage(msg, max_chars_per_message=2048):
		"""
		Breaks a message that is too long.
		:param max_chars_per_message: maximum amount of characters per message.
		The official maximum is 4096.
		Changing this is not recommended.
		:param msg: message to be split
		:return: a list of message pieces
		"""

		# let's split the message by newlines first
		message_split = msg.split("\n")

		# the result will be stored here
		broken = []

		# splitting routine
		while message_split:
			result = message_split.pop(0) + "\n"
			if len(result) > max_chars_per_message:
				# The chunk is huge. Split it not caring for newlines.
				broken += [result[i:i+max_chars_per_message].strip("\n\t\r ")
						   for i in range(0,len(result),max_chars_per_message)]
			else:
				# It's a smaller chunk, append others until their sum is bigger than maximum
				while len(result) <= max_chars_per_message:
					if not message_split:
						# if the original ran out
						break
					# check if the next chunk makes the merged chunk it too big
					if len(result) + len(message_split[0]) <= max_chars_per_message:
						# nope. append chunk
						result += message_split.pop(0) + "\n"
					else:
						# yes, it does. Stop on this.
						break
				broken += [result.strip("\n\t\r ")]

		return broken

	def sendMessage(self, chat_id, message, key_markup="SAME", keyboard_short=True, preview=True, markdown=None, reply_to=None):
		"""
		Sends a text message to Telegram user
		:param keyboard_short: If True, the buttons on custom keyboard will be lower in height.
		Might be useful if there are many rows of buttons and the kyboard fills the screen.
		:param chat_id: ID of chat
		:param message: text to send
		:param key_markup: a list representing a custom keyboard markup to show to user.
		If "SAME", use the same markup as before.
		If None, hide the custom keyboard.
		:param preview: Should a link in a message generate a page preview within a message?
		:type preview: bool
		:param markdown: Should a message support markdown formatting or htmls formatting?
		Pass "html" for HTML formatting, or True for markdown formatting.
		:param reply_to: An id of an existing message. A sent message will be a reply to that message.
		:return: None
		"""
		def markup(m):
			if not m:
				return telegram.ReplyKeyboardHide()
			elif m == "SAME":
				return None
			else:
				return telegram.ReplyKeyboardMarkup(m, resize_keyboard=keyboard_short)

		markdown_mode = None
		if markdown == "html":
			markdown_mode = telegram.ParseMode.HTML
		elif markdown:
			markdown_mode = telegram.ParseMode.MARKDOWN

		logging.warning("Replying to " + str(chat_id) + ": " + message)
		fulltext = self.breakLongMessage(message)

		def send(text):
			self.bot.sendMessage(chat_id=chat_id,
					text=text,
					parse_mode=markdown_mode,
					disable_web_page_preview=(not preview),
					reply_markup=markup(key_markup),
					reply_to_message_id=reply_to
					)

		for text in fulltext:
			# iterating over parts of a long split message
			while True:
				try:
					if text:
						self.bot.sendChatAction(chat_id, telegram.ChatAction.TYPING)
						send(text=text)
				except telegram.error.NetworkError as e:
					if "Bad request: can't parse message text: can't find end of the entity" in str(e):
						self.sendMessage(chat_id=chat_id, message=self.escape_markdown(text),
										 key_markup=key_markup, keyboard_short=keyboard_short,
										 preview=preview, markdown=markdown, reply_to=reply_to)
				except KeyboardInterrupt:
					raise KeyboardInterrupt
				except Exception as e:
					if "Message is too long" in str(e):
						self.sendMessage(chat_id=chat_id, message="Error: Message is too long!")
					elif ("urlopen error" in str(e)) or ("timed out" in str(e)):
						logging.error("Could not send message. Retrying! Error: " +
							full_traceback()
							)
						sleep(3)
						continue
					else:
						logging.error(
								"Could not send message. Error: " + full_traceback())
				break

	def sendPic(self, chat_id, pic, caption=None):
		"""
		Sends a picture in a Telegram message to a user. Retries if fails.
		:param chat_id: ID of chat
		:param pic: a picture file (an object created with open() ) or a bytestring
		:param caption: a text that goes together with picture ina message.
		:return: None
		"""
		sent_message_id = None
		while True:
			try:
				logging.debug("Picture: " + str(pic))
				self.bot.sendChatAction(chat_id, telegram.ChatAction.UPLOAD_PHOTO)
				# set file read cursor to the beginning.
				# This ensures that if a file needs to be re-read (may happen due to exception), it is read from the beginning.
				if hasattr(pic, "seek"):
					# It is probably a file
					pic.seek(0)
				else:
					if isinstance(pic, bytes):
						# It is a bytestring
						pic = io.BufferedReader(io.BytesIO(pic))
					else:
						#a string, probably a file_id. leave as-is
						pass

				# Send the picture!
				sent_message_id = self.bot.sendPhoto(chat_id=chat_id, photo=pic, caption=caption)
			except KeyboardInterrupt:
				raise KeyboardInterrupt
			except AttributeError:
				logging.error("Could not send photo. Bad object!\n" + full_traceback())
			except FileNotFoundError:
				logging.error("Could not send photo. File not found!\n" + full_traceback())
			except Exception as e:
				if ("urlopen error" in str(e)) or ("timed out" in str(e)):
					logging.error("Could not send photo. Retrying! Error: " +
						full_traceback()
						)
					sleep(3)
					continue
				else:
					# raise Exception("Could not send message. rror: " + full_traceback())
					logging.error(
							"Could not send photo. Unknown error: " + full_traceback())
			break
		return sent_message_id

	def getUpdates(self):
		"""
		Gets updates. Updates are basically messages sent to bot from users.
		Retries if it fails.
		:return: a list of update objects
		"""
		# if getting updates fails - retry
		updates = []
		while True:
			try:
				updates = self.bot.getUpdates(offset=self.LAST_UPDATE_ID)
				pass
			except KeyboardInterrupt:
				raise KeyboardInterrupt
			except Exception:
				logging.error("Could not read updates. Retrying! Error: " + full_traceback())
				sleep(1)
				continue
			break
		return updates

	def getFileID(self, update, photoIndex=-1):
		"""
		Gets the file_id of a file contained in a message. Empty string if there is no file.
		:param update: update object containing a message.
		:param photoIndex: a photo message contains a picture in various resolutions.
		This determines which one should be picked.
		By default it is the last one, which has the highest resolution.
		:return: file_id
		"""
		if self.isPhoto(update):
			file_id = update.message.photo[photoIndex]['file_id']
		elif self.isDocument(update):
			file_id = update.message.document['file_id']
		else:
			file_id = ""

		return file_id

	def getFileID_byMesssageObject(self, message, photoIndex=-1):
		"""
		Gets the file_id of a file contained in a message. Empty string if there is no file.
		:param message: message object containing a message.
		:param photoIndex: a photo message contains a picture in various resolutions.
		This determines which one should be picked.
		By default it is the last one, which has the highest resolution.
		:return: file_id
		"""
		if self.messageIsPhoto(message):
			file_id = message.photo[photoIndex]['file_id']
		elif self.messageIsDocument(message):
			file_id = message.document['file_id']
		else:
			file_id = ""

		return file_id

	def getFileByID(self, file_id):
		"""
		Gets a `File` object based on file_id.
		:param file_id:
		:return: `File`
		"""
		return self.bot.getFile(file_id)

	def getFileByUpdate(self, update, photoIndex=-1):
		"""
		Gets a `File` object based on update object.
		:param update: update object containing a message.
		:param photoIndex: a photo message contains a picture in various resolutions.
		This determines which one should be picked.
		By default it is the last one, which has the highest resolution.
		:return: `File`
		"""
		file_id = self.getFileID(update, photoIndex)
		return self.getFileByID(file_id)

	def getFullPath(self, update, photoIndex=-1):
		"""
		Gets a full path (URL) of a file contained in a message.
		:param update: update object containing a message.
		:param photoIndex: a photo message contains a picture in various resolutions.
		This determines which one should be picked.
		By default it is the last one, which has the highest resolution.
		:return: full URL path to file
		"""
		File = self.getFileByUpdate(update, photoIndex)
		pth = File.file_path
		return pth

	def getFullName(self, update, photoIndex=-1):
		"""
		Gets a filename (with extension) which is assigned by Telegram to a file contained in a message.
		:param update: update object containing a message.
		:param photoIndex: a photo message contains a picture in various resolutions.
		This determines which one should be picked.
		By default it is the last one, which has the highest resolution.
		:return: full neame of a file
		"""
		pth = self.getFullPath(update, photoIndex)
		full_name = path.basename(pth)
		return full_name

	def getURLFileName(self, update, photoIndex=-1):
		"""
		Gets a filename (without extension) which is assigned by Telegram to a file contained in a message.
		:param update: update object containing a message.
		:param photoIndex: a photo message contains a picture in various resolutions.
		This determines which one should be picked.
		By default it is the last one, which has the highest resolution.
		:return: file name without extension
		"""
		full_name = self.getFullName(update, photoIndex)
		file_name = path.splitext(full_name)[0]
		return file_name

	def getFileExt(self, update, photoIndex=-1, no_dot=False):
		"""
		Gets a filename (without extension) which is assigned by Telegram to a file contained in a message.
		:param update: update object containing a message.
		:param photoIndex: a photo message contains a picture in various resolutions.
		This determines which one should be picked.
		By default it is the last one, which has the highest resolution.
		:param no_dot: removes a dot from file extension if True.
		:return: file extension
		"""
		pth = self.getFullPath(update, photoIndex)
		file_ext = path.splitext(pth)[1]
		if no_dot:
			file_ext = file_ext.replace(".", "")
		return file_ext

	@staticmethod
	def getDocumentFileName(update):
		"""
		Returns a filename (with extension) of a document (File) in a message.
		It is the original name of a file, not the one that Telegram assigns to files.
		Works only for file messages (not photo, text, etc.)
		:param update: an update object containing a message
		:return: a filename (with extension). Or empty string if update is not a document
		"""
		try:
			document = update.message.document
			if document:
				return document["file_name"]
			else:
				return ""
		except AttributeError:
			return ""

	def getFileSize(self, update):
		"""
		Returns the size of a file in a message.
		:param update: an update object containing a message
		:return: file size
		"""

		file_id = self.getFileID(update)
		File = self.getFileByID(file_id)
		file_size = File['file_size']
		return file_size

	def downloadFile(self, file_id, custom_filepath=None):
		"""
		Downloads the file with the given file_id to a specified location.
		It can be from any type of message (Photo, Document, etc.)
		:param file_id:
		:param custom_filepath: A full path where a file should be saved.
		If nothing is specified, it will be saved to current folder with a name that Telegram assigned to it.
		Note: the extension specified in custom_filepath is ignored.
		It is assigned automatically depending on the original extension (Document)
		or the one Telegram assigned to a file (Photo)
		:return: None
		"""
		File = self.bot.getFile(file_id)
		if custom_filepath:
			# finding out the extension of an image file on Telegram server
			file_name_with_path, file_ext = path.splitext(File.file_path)
			# directory path to save image to
			directory = path.dirname(custom_filepath)
			# gluing together a filepath and extension, overriding one specified in arguments
			custom_filepath = path.splitext(custom_filepath)[0] + file_ext
			# create a directory if it doesn't exist
			if directory:
				makedirs(directory, exist_ok=True)
		# download the file to a given directory
		File.download(custom_path=custom_filepath)

	def start(self, processingFunction=None, periodicFunction=None,
			termination_function=None, slp=0.1):
		"""
		Starts the main loop, which can handle termination on `KeyboardInterrupt` (e.g. Ctrl+C)
		:param processingFunction: a function that is invoked in a current iteration of the loop
		only if there are updates. An `update` argument containing a message object is passed to it.
		:param periodicFunction: a function that is invoked in every iteration of the loop
		regardless of presence of updates.
		:param termination_function: a function that is invoked when the loop is terminated by user.
		:param slp: a pause between loops to decrease load.
		:return: None
		"""
		while True:
			try:
				# a function that is called regardless of updates' presence
				if periodicFunction:
					periodicFunction()
				self._updateProcessing(processingFunction=processingFunction)
				sleep(slp)
			except KeyboardInterrupt:
				print("Terminated by user!")
				if termination_function:
					termination_function()

				# this ensures that LAST_UPDATE_ID is updated
				#  or else it will process already processed messages after restart
				self.getUpdates()
				break

	def _updateProcessing(self, processingFunction=None):
		"""
		This function gets updates, passes them to `processingFunction` and updates the LAST_UPDATE_ID.
		:param processingFunction: a function that is invoked in a current iteration of the loop
		only if there are updates. An `update` argument containing a message object is passed to it.
		:return: None
		"""

		# basically, messages sent to bot
		updates = self.getUpdates()

		# main message processing routine
		for update in updates:
			logging.warning("Received message: " + str(
					update.message.chat_id) + " " + update.message.from_user.username + " " + update.message.text)

			# a functions that processes updates, one by one
			if processingFunction:
				processingFunction(update)

			# Updates global offset to get the new updates
			self.LAST_UPDATE_ID = update.update_id + 1

if __name__ == '__main__':
	with open("tests/testbot_token", "r") as f:
		BOT_TOKEN = f.read()
	bot = TelegramHigh(BOT_TOKEN)
	u = bot.getUpdates()[-1]
	print(u)
	file_id = bot.getFileID(u)
	print(file_id, type(file_id))