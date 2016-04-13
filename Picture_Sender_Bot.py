#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

#check if the version of Python is correct
import io

from python_version_check import check_version

check_version((3, 4, 3))

VERSION_NUMBER = (1, 0, 6)

import logging
import telegram
from os import path, listdir, walk, remove as file_remove
from random import choice
from time import time, sleep
from itertools import chain
import socket
import pickle #module for saving dictionaries to file
import requests, json
from threading import Thread
from queue import Queue

from traceback_printer import full_traceback
from telegramHigh import TelegramHigh
from textual_data import *
from userparams import UserParams
from language_support import LanguageSupport
import utils
from file_db import FileDB


############
##PARAMETERS
############

#How often should a file list of images be updated
FILE_UPDATE_PERIOD = 600

#If true, use dropbox. If false, use local filesystem
FROM_DROPBOX = False

#A minimum and maximum picture sending period a user can set
MIN_PICTURE_SEND_PERIOD = 1
MAX_PICTURE_SEND_PERIOD = 86400

#A default send period
PICTURE_SEND_PERIOD = 600


INITIAL_SUBSCRIBER_PARAMS = {"lang": "EN",  # bot's langauge
							 "subscribed": 0, # has the user subscribed?
							 "period": PICTURE_SEND_PERIOD,
							 "last_update_time" : 0
							 }




MAIN_MENU_KEY_MARKUP = [
[SUBSCRIBE_BUTTON,UNSUBSCRIBE_BUTTON],
[GIMMEPIC_BUTTON],
[HELP_BUTTON, ABOUT_BUTTON, OTHER_BOTS_BUTTON]
]

################
###GLOBALS######
################





#############
##METHODS###
############

###############
###CLASSES#####
###############

class MainPicSender():
	"""The bot class"""

	LAST_UPDATE_ID = None

	# Dictionary containing handles to picture-sending processes
	pic_sender_threads = {}

	def __init__(self, token):
		super(MainPicSender, self).__init__()
		self.bot = TelegramHigh(token)

		# Initialize user parameters database
		self.userparams = UserParams("users", initial=INITIAL_SUBSCRIBER_PARAMS)

		# Initialize file database
		self.file_db = FileDB("files")

		#get list of all image files
		self.updateFileListThread()

		# Initialize List of files
		self.files = []

		self.bot.start(processingFunction=self.processUpdate, periodicFunction=self.periodicRoutine)

	def processUpdate(self, u):
		bot = self.bot
		Message = u.message
		message = Message.text
		message_id = Message.message_id
		chat_id = Message.chat_id
		subs = self.userparams

		# initialize the user's params if they are not present yet
		subs.initializeUser(chat_id=chat_id, data=INITIAL_SUBSCRIBER_PARAMS)

		# language support class for convenience
		LS = LanguageSupport(subs.getEntry(chat_id=chat_id, param="lang"))
		lS = LS.languageSupport
		allv = LS.allVariants
		MMKM = lS(MAIN_MENU_KEY_MARKUP)

		if message == "/start":
			bot.sendMessage(chat_id=chat_id
				,message=lS(START_MESSAGE)
				,key_markup=MMKM
				)
		elif message == "/help" or message == HELP_BUTTON:
			bot.sendMessage(chat_id=chat_id
				,message=lS(HELP_MESSAGE).format(str(MIN_PICTURE_SEND_PERIOD),str(MAX_PICTURE_SEND_PERIOD))
				,key_markup=MMKM
				,markdown=True
				)
		elif message == "/about" or message == ABOUT_BUTTON:
			bot.sendMessage(chat_id=chat_id
				,message=lS(ABOUT_MESSAGE).format(".".join([str(i) for i in VERSION_NUMBER]))
				,key_markup=MMKM
				,markdown=True
				)
		elif message == "/otherbots" or message == lS(OTHER_BOTS_BUTTON):
			bot.sendMessage(chat_id=chat_id
				,message=lS(OTHER_BOTS_MESSAGE)
				,key_markup=MMKM
				,markdown=True
				)
		elif message == "/subscribe" or message == SUBSCRIBE_BUTTON:
			period = self.userparams.getEntry(chat_id, "period")
			if self.userparams.getEntry(chat_id, "subscribed") == 0:
				self.userparams.setEntry(chat_id, "subscribed", 1)
				self.userparams.setEntry(chat_id, "last_update_time", time())

				bot.sendMessage(chat_id=chat_id,
					message="""You're subscribed now! 
An image will be sent to you every {0} seconds. 
To cancel subscription enter /unsubscribe. 
To change the period of picture sending type a number.""".format(period),
					key_markup=MMKM
					)
			else:
				bot.sendMessage(chat_id=chat_id,
					message="""You have already subscribed!
To cancel subscription enter /unsubscribe.
To change the period of picture sending type a number.
Your current period is {0} seconds.""".format(period),
					key_markup=MMKM
					)
		elif message == "/unsubscribe" or message == UNSUBSCRIBE_BUTTON:
			if self.userparams.getEntry(chat_id, "subscribed") == 1:
				self.userparams.setEntry(chat_id, "subscribed", 0)
				bot.sendMessage(chat_id=chat_id,
					message="You have unsubscribed. To subscribe again type /subscribe",
					key_markup=MMKM
					)
			else:
				bot.sendMessage(chat_id=chat_id,
					message="You haven't subscribed yet! To subscribe type /subscribe",
					key_markup=MMKM
					)
		elif message == "/gimmepic" or message == GIMMEPIC_BUTTON:
			self.startRandomPicThread(chat_id)
		else:
			#any other message
			try:
				new_period = int(message)

				if self.userparams.getEntry(chat_id,"subscribed") == 0:
					bot.sendMessage(chat_id=chat_id,
									message="You're not subscribed yet! /subscribe first!"
									,key_markup=MMKM
									)
				else:
					#If a period is too small
					if new_period < MIN_PICTURE_SEND_PERIOD:
						self.userparams.setEntry(chat_id, "period", MIN_PICTURE_SEND_PERIOD)
						bot.sendMessage(chat_id=chat_id,
							message="The minimum possible period is {0}.\nSetting period to {0}.".format(str(MIN_PICTURE_SEND_PERIOD))
							,key_markup=MMKM
							)


					#If a period is too big
					elif new_period > MAX_PICTURE_SEND_PERIOD:
						self.userparams.setEntry(chat_id, "period", MAX_PICTURE_SEND_PERIOD)
						bot.sendMessage(chat_id=chat_id,
							message="The maximum possible period is {0}.\nSetting period to {0}.".format(str(MAX_PICTURE_SEND_PERIOD))
							,key_markup=MMKM
							)

					#If a period length is fine - accept
					else:
						self.userparams.setEntry(chat_id, "period", new_period)
						bot.sendMessage(chat_id=chat_id,
							message="Setting period to " + str(new_period) + "."
							,key_markup=MMKM
							)

					# Reset timer
					self.userparams.setEntry(chat_id, "last_update_time", int(time()))

			#user has sent a bullsh*t command
			except ValueError:
				bot.sendMessage(chat_id=chat_id,
					message="Unknown command!"
					,key_markup=MMKM
					)

	def periodicRoutine(self):
		'''
		A function that runs every second or so
		:return:
		'''
		# Update list of picture paths
		if not hasattr(self, 'update_filelist_thread_queue'):
			# Init queue
			self.update_filelist_thread_queue = Queue()
		while not self.update_filelist_thread_queue.empty():
			# update params from thread
			q = self.update_filelist_thread_queue.get()
			self.last_filelist_update_time = q[0]
			print("self.last_filelist_update_time", self.last_filelist_update_time)#debug

		self.updateFileListThread()

		# TODO:Clean up finished pic sender threads

		# subscription handling
		for user in self.userparams.getAllEntries(fields=["subscribed","period","last_update_time","chat_id"]):
			if user[0] == 1:
				# user is subscribed
				cur_time = time()
				if (cur_time - user[2]) > user[1]:
					# The time has come for this user (heh, sounds intimidating)
					self.startRandomPicThread(user[3])
					# Reset the timer
					self.userparams.setEntry(user[3],"last_update_time", cur_time)




	def updateFileListThread(self):
		'''
		Starts the file list grabbing thread
		:return:
		'''
		if not hasattr(self, 'last_filelist_update_time') or (time()-self.last_filelist_update_time) >  FILE_UPDATE_PERIOD:
			# Run updater is it's time already
			if hasattr(self, 'last_filelist_update_time'):
				print('time()-self.last_filelist_update_time)',(time()-self.last_filelist_update_time))#debug
			if not (hasattr(self, 'filelist_updater_thread') and self.filelist_updater_thread.isAlive()):
				# Run the thread if it is not working yet (never existed or already terminated, respectively).
				print("starting file updater")#debug
				self.filelist_updater_thread = Thread(target=self.updateFileList)
				self.filelist_updater_thread.start()
			else:
				pass
				print("updater already running!")#debug

	def fileToDB(self, filepath, mod_time):
		"""
		Adds or updates a file in the database
		:param mod_time: When the real file was modified, in Unix time
		:param filepath: a full path to a file to process
		:return:
		"""
		file_db = self.file_db

		# print("fileToDB", filepath, mod_time)#debug

		if path.splitext(filepath)[1].replace(".", "").lower() != "txt":
			# it's an image
			if not file_db.fileExists(filepath):
				file_db.addFile(filepath, mod_time=mod_time)
			elif mod_time > file_db.getModTime(filepath):
				#file has updated, invalidate the cached telegram file ID and update the mod time in DB
				file_db.invalidateCached(filepath)
				file_db.updateModTime(filepath, mod_time)
		else:
			#TODO: read metadata from dropbox
			# it's a text file
			if path.basename(filepath) == METADATA_FILENAME:
				#it's a metadata file
				def getMetadata():
					# Update the obsolete metadata
					metadata = ""
					try:
						if not FROM_DROPBOX:
							with open(filepath, 'r') as f:
								metadata = f.read()
						else:
							metadata = self.getDropboxFile(filepath).decode()
							print("Dropbox metadata", metadata)#debug
					except Exception as e:
						logging.error("Could not read metafile!", full_traceback())
					return metadata
				if not file_db.fileExists(filepath):
					# add a folder entry with metadata. Path in DB will be the full path to metadata text file
					file_db.addMetafile(filepath, getMetadata(), mod_time)
				elif mod_time > file_db.getModTime(filepath):
					file_db.updateMetadata(filepath, getMetadata(), mod_time)


	def checkFilesForDeletion(self, files):
		"""
		Checks the database for the presence of files that don't exist anymore.
		:param files: list of files received from an actual filesystem scan
		:return:
		"""
		file_db = self.file_db

		# Get a list of paths in database
		DB_files = file_db.getFileList()

		for f in DB_files:
			if not f in files:
				file_db.deleteFile(f)


	def updateFileList(self):
		'''
		THREAD
		Reads the files in the directory and updates the file list
		'''

		if not FROM_DROPBOX:
			# list of filepaths
			files = utils.FolderSearch.getFilepathsInclSubfolders(PIC_FOLDER, allowed_extensions=["txt","png","jpg","jpeg"])

			# When the file was modified, in Unix time
			# list of tuples (filepath, mod_time)
			files_and_mods = list(zip(files,
				[utils.FileUtils.getModificationTimeUnix(f) for f in files]
			))
		else:
			files_and_mods = utils.DropboxFolderSearch.getFilepathsInclSubfoldersDropboxPublic(DROPBOX_FOLDER_LINK,
																							   DROPBOX_APP_KEY,
																							   DROPBOX_SECRET_KEY,
																							   unixify_mod_time=True
																							   )
			files = [i[0] for i in files_and_mods]

		print("files_and_mods",files_and_mods)#debug



		# Add or update files to DB
		for i in files_and_mods:
			print(i)#debug
			self.fileToDB(i[0], i[1])

		# Delete files that no longer exist from DB
		self.checkFilesForDeletion(files)

		# Update the time
		last_filelist_update_time=time()

		# sleep(5)#debug
		print("file list got!")#debug
		print("files", files)#debug
		print("last_filelist_update_time",last_filelist_update_time)#debug

		# Put results to queue
		self.update_filelist_thread_queue.put((last_filelist_update_time,))

	@staticmethod
	def getDropboxFile(filepath):
		"""
		Gets the data from a file in Dropbox
		:param filepath: path to a file in Dropbox
		:return:  bytestring containing data from file
		"""
		data = None
		# First, get metadata of a file. It contains a direct link to it!
		req=requests.post('https://api.dropbox.com/1/metadata/link',
						  data=dict( link=DROPBOX_FOLDER_LINK,
									 client_id=DROPBOX_APP_KEY,
									 client_secret=DROPBOX_SECRET_KEY,
									 path=filepath), timeout=5 )
		if req.ok:
			# If metadata got grabbed, extract a link to a file and make a downloadable version of it
			req= json.loads(req.content.decode())['link'].split("?")[0] + "?dl=1"
			# Now let's get the file contents
			try:
				req=requests.get(req, timeout=5)
				if req.ok:
					data = req.content
			except:
				data = None
		else:
			#handle absence of file (maybe got deleted?)
			data = None

		return data

	def startRandomPicThread(self, chat_id):
		"""
		Starts a random pic sending thread
		:param chat_id: a user to send pic to
		:return:
		"""
		def startThread(chat_id):
			t = Thread(target=self.sendRandomPic, args=(chat_id,))
			self.pic_sender_threads[chat_id] = t
			t.start()

		try:
			if not self.pic_sender_threads[chat_id].isAlive():
				# Start the thread if it is dead
				startThread(chat_id)
			else:
				self.bot.sendMessage(chat_id=chat_id,
					message="I'm still sending you a pic. Please wait!"
					)
		except KeyError:
			# If there was never a thread for this user, start it.
			startThread(chat_id)

	def sendRandomPic(self, chat_id):
		"""
		THREAD
		Sends a random picture from a file list to a user.
		:param chat_id:
		:return:
		"""
		def getLocalFile(filepath):
			"""
			Gets the data from a local file
			:param filepath: path to a local file to get data
			:return: bytestring containing data from file
			"""
			with open(filepath, 'rb') as f:
				data = f.read()

			return data


		sent_message, cached_ID, data, random_file, caption = None, None, None, None, ""
		while True:
			try:
				# get list of files
				files = self.file_db.getFileListPics()
				# pick a file at random
				random_file = choice(files)
			except IndexError:
				# DB is empty. Exit the function
				self.bot.sendMessage(chat_id=chat_id,
									 message="Sorry, no pictures were found!"
									 )
				return

			# get the ID of a file in Telegram, if present
			cached_ID = self.file_db.getFileCacheID(random_file)
			# Get the metadata to send with a pic
			caption = self.file_db.getCaptionPic(random_file)

			while True:
				if not cached_ID:
					# if file is not cached in Telegram
					try:
						# We will send a bytestring
						if not FROM_DROPBOX:
							data = getLocalFile(random_file)
							print("Not cached, getting a local file!")#debug
						else:
							# data = None
							print("Not cached, getting a file from Dropbox!")#debug
							data = self.getDropboxFile(random_file)

					except Exception as e:
						logging.error("Error reading file!" + full_traceback())
						#File still exists in the DB, but is gone for real. Try another file.
						break
				else:
					# file is cached, use resending of cache
					data = cached_ID
					print("Cached, sending cached file!")

				try:
					# Send the pic and get the message object to store the file ID
					sent_message = self.bot.sendPic(chat_id=chat_id,
									pic=data,
									caption=caption
									)
					# print("sent_message", sent_message)#debug
					break
				except Exception as e:
					if "Network error" in str(e):
						print("Cache damaged! Trying to send image by uploading!")
						# cached ID is invalid. Remove it and upload the image.
						self.file_db.invalidateCached(random_file)
						cached_ID = None

			if not data:
				# If there is no data, the file could not be read. Come back to the beginning of the loop
				# and try picking a different random file
				continue
			else:
				# Data exists and was sent, exit loop
				break


		if sent_message == None:
			self.bot.sendMessage(chat_id=chat_id,
							 message="Error sending image! Please, try again!"
							 )
		elif not cached_ID:
			print("sent_message",sent_message, type(sent_message))#debug
			file_id = self.bot.getFileID_byMesssageObject(sent_message)
			print("Assigning cache!", file_id)#debug
			self.file_db.updateCacheID(random_file, file_id)


########################################
		##########################################
		################################


	#
	# def sendPicProcess(self,chat_id,pic,caption=None):
	# 	self.sendPic(chat_id=chat_id,pic=pic,caption=caption)
	#
	# def sendRandomPic(self,chat_id,queue):
	# 	if not FROM_DROPBOX:
	# 		###########
	# 		###from local filesystem
	# 		##############
	# 		random_pic_path = ""
	# 		while not (path.splitext(random_pic_path)[1].lower() in ['.jpg', '.jpeg', '.gif', '.png', '.tif', '.bmp']):
	# 			#filtering. Only images should be picked
	# 			random_pic_path = choice( self.files )
	# 		metadata=""
	# 		#try sending metadata if present. Skip if not.
	# 		try:
	# 			with open( path.join( path.abspath(path.join(random_pic_path, path.pardir)), METADATA_FILENAME), "r") as metafile:
	# 				metadata=metafile.read()
	# 		except FileNotFoundError:
	# 			pass
	#
	# 		with open( random_pic_path,"rb" ) as pic:
	# 			logging.warning("Sending image to " + str(chat_id) + " " + str(pic))
	# 			self.sendPic(chat_id,pic,caption=metadata)
	#
	#
	# 	else:
	# 		############
	# 		#from dropbox
	# 		###########
	# 		while True:
	# 			random_pic_path = ""
	# 			while not (path.splitext(random_pic_path)[1].lower() in ['.jpg', '.jpeg', '.gif', '.png', '.tif', '.bmp']):
	# 				#filtering. Only images should be picked
	# 				random_pic_path = choice( self.files )
	# 				tmp_path = path.join("/tmp/", path.basename(random_pic_path) )
	# 			#First, get metadata of a file. It contains a direct link to it!
	# 			req=requests.post('https://api.dropbox.com/1/metadata/link',data=dict( link=DROPBOX_FOLDER_LINK, client_id=DROPBOX_APP_KEY,client_secret=DROPBOX_SECRET_KEY, path=random_pic_path), timeout=10 )
	# 			if req.ok:
	# 				#If metadata got grabbed, extract a link to a file and make a downloadable version of it
	# 				req= json.loads(req.content.decode())['link'].split("?")[0] + "?dl=1"
	# 				#now let's get the file contents
	# 				try:
	# 					req=requests.get(req,timeout=30)
	# 					if req.ok:
	# 						req= req.content
	# 						break
	# 				except:
	# 					pass
	#
	# 			else:
	# 				#handle absence of file (maybe got deleted?)
	# 				pass
	#
	# 		metadata=""
	# 		#try to read metadata
	# 		try:
	# 			meta_req=requests.post('https://api.dropbox.com/1/metadata/link',data=dict( link=DROPBOX_FOLDER_LINK, client_id=DROPBOX_APP_KEY,client_secret=DROPBOX_SECRET_KEY, path=path.join(path.dirname(random_pic_path),METADATA_FILENAME ) ) , timeout=10)
	# 			if meta_req.ok:
	# 					meta_req= json.loads(meta_req.content.decode())['link'].split("?")[0] + "?dl=1"
	# 					meta_req = requests.get(meta_req,timeout=10)
	# 					metadata = meta_req.content.decode()
	# 			else:
	# 				metadata=""
	# 		except:
	# 			metadata=""
	# 			pass
	#
	# 		with open(tmp_path, 'wb') as tmppic:
	# 			#now let's save the file to temporary
	# 			tmppic.write(req)
	#
	# 		with open(tmp_path, 'rb') as pic:
	# 			#send the file
	#
	# 			for att in range(3):
	# 				logging.warning("Attempt " + str(att+1) + " of sending image to " + str(chat_id) + " " + str(pic))
	# 				p = Process(target=self.sendPicProcess,args=(chat_id,pic,metadata,))
	# 				p.start()
	#
	# 				#wait 5 seconds then repeat attempt. Exit loop if process has terminated.
	# 				startTime = time()
	# 				while time() - startTime < 5:
	# 					if not p.is_alive():
	# 						break
	#
	# 				if not p.is_alive():
	# 					break
	# 				else:
	# 					p.terminate()
	# 			else:
	# 				self.sendMessage(chat_id=chat_id,text="Failed to send picture. Please try again!")
	#
	# 		# delete temporary file
	# 		file_remove(tmp_path)
	#
	#
	# def echo(self):
	# 	bot = self.bot
	#
	# 	def startRandomPicProcess(chat_id):
	# 		'''
	# 		Starts and image sending process.
	# 		'''
	# 		def startProcess():
	# 			q = Queue()
	# 			p = Process(target=self.sendRandomPic,args=(chat_id,q,))
	# 			self.processes[chat_id]=(p,q)
	# 			p.start()
	# 		try:
	# 			if self.processes[chat_id][0].is_alive():
	# 				#the process is still working
	# 				self.sendMessage(chat_id=chat_id
	# 					,text="I'm still sending you a picture. Please wait!"
	# 					)
	# 			else:
	# 				#the process entry exists but the process is terminated. Very improbable.
	# 				startProcess()
	# 		except KeyError:
	# 			startProcess()
	#
	# 	#clean the image-getting processes that have terminated
	# 	tempProcesses=dict(self.processes) #because error occurs if dictionary changes size during loop
	# 	for i in tempProcesses:
	# 		if not self.processes[i][0].is_alive():
	# 			del self.processes[i]
	#
	# 	#check if it is time to update the file list
	# 	if time() - self.last_update_time > FILE_UPDATE_PERIOD:
	# 		self.updateFileList()
	#
	# 	#check if it is time to send an image already
	# 	for i in self.subscribers:
	# 		if (time() - self.subscribers[i][1]) > self.subscribers[i][0]:
	# 			#The time has come for this user (heh, sounds intimidating)
	# 			startRandomPicProcess(i)
	# 			#Reset user's timer
	# 			self.subscribers[i][1] = time()
	# 			#Save to file
	# 			self.saveSubscribers()
	#
	# 	#if getting updates fails - retry
	# 	while True:
	# 		try:
	# 			updates = bot.getUpdates(offset=self.LAST_UPDATE_ID, timeout=3)
	# 		except Exception as e:
	# 			logging.error("Could not read updates. Retrying! Error: " + str(e))
	# 			continue
	# 		break
	#
	# 	for update in updates:
	# 		chat_id = update.message.chat_id
	# 		Message = update.message
	# 		from_user = Message.from_user
	# 		message = Message.text
	# 		logging.warning("Received message: " + str(chat_id) + " " + from_user.username + " " + message)
	#
	# 		if message == "/start":
	# 			self.sendMessage(chat_id=chat_id
	# 				,text=START_MESSAGE
	# 				)
	# 		elif message == "/help" or message == HELP_BUTTON:
	# 			self.sendMessage(chat_id=chat_id
	# 				,text=HELP_MESSAGE
	# 				)
	# 		elif message == "/about" or message == ABOUT_BUTTON:
	# 			self.sendMessage(chat_id=chat_id
	# 				,text=ABOUT_MESSAGE
	# 				)
	# 		elif message == "/otherbots" or message == self.languageSupport(chat_id,OTHER_BOTS_BUTTON):
	# 			self.sendMessage(chat_id=chat_id
	# 				,text=self.languageSupport(chat_id,OTHER_BOTS_MESSAGE)
	# 				)
	# 		elif message == "/subscribe" or message == SUBSCRIBE_BUTTON:
	# 			if not chat_id in self.subscribers:
	# 				self.subscribers[chat_id] = [PICTURE_SEND_PERIOD,time()]
	# 				self.saveSubscribers()
	# 				self.sendMessage(chat_id=chat_id,
	# 					text="You're now subscribed. The default period of image sending is " + str(PICTURE_SEND_PERIOD) + " seconds. To cancel subscription enter /unsubscribe. To change the period of picture sending type a number.",
	# 					)
	# 			else:
	# 				self.sendMessage(chat_id=chat_id,
	# 					text="You have already subscribed. To cancel subscription enter /unsubscribe. To change the period of picture sending type a number.\nYour current period is " + str(self.subscribers[chat_id][0])+ " seconds.",
	# 					)
	# 		elif message == "/unsubscribe" or message == UNSUBSCRIBE_BUTTON:
	# 			try:
	# 				del self.subscribers[chat_id]
	# 				self.saveSubscribers()
	# 				self.sendMessage(chat_id=chat_id,
	# 					text="You have unsubscribed. To subscribe again type /subscribe",
	# 					)
	# 			except KeyError:
	# 				self.sendMessage(chat_id=chat_id,
	# 					text="You are not on the list, there is nowhere to unsubscribe you from. To subscribe type /subscribe",
	# 					)
	# 		elif message == "/gimmepic" or message == GIMMEPIC_BUTTON:
	# 			startRandomPicProcess(chat_id)
	# 		else:
	# 			#any other message
	# 			try:
	# 				self.subscribers[chat_id]#check if user has subscribed
	# 				new_period = int(message)
	#
	# 				#If a period is too small
	# 				if new_period < MIN_PICTURE_SEND_PERIOD:
	# 					self.subscribers[chat_id][0] = MIN_PICTURE_SEND_PERIOD
	# 					self.sendMessage(chat_id=chat_id,
	# 						text="The minimum possible period is " + str(MIN_PICTURE_SEND_PERIOD) + ".\nSetting period to " + str(MIN_PICTURE_SEND_PERIOD) + "."
	# 						)
	# 					self.subscribers[chat_id][1] = time()
	#
	# 				#If a period is too big
	# 				elif new_period > MAX_PICTURE_SEND_PERIOD:
	# 					self.subscribers[chat_id][0] = MAX_PICTURE_SEND_PERIOD
	# 					self.sendMessage(chat_id=chat_id,
	# 						text="The maximum possible period is " + str(MAX_PICTURE_SEND_PERIOD) + ".\nSetting period to " + str(MAX_PICTURE_SEND_PERIOD) + "."
	# 						)
	# 					self.subscribers[chat_id][1] = time()
	#
	# 				#If a period length is fine - accept
	# 				else:
	# 					self.subscribers[chat_id][0] = new_period
	# 					self.sendMessage(chat_id=chat_id,
	# 						text="Setting period to " + str(new_period) + "."
	# 						)
	# 					self.subscribers[chat_id][1] = time()
	#
	# 				#A new period should be saved to file
	# 				self.saveSubscribers()
	#
	# 			#user not in list, not subscribed
	# 			except KeyError:
	# 				self.sendMessage(chat_id=chat_id,
	# 					text="You're not subscribed yet! /subscribe first!"
	# 					)
	#
	# 			#user has sent a bullsh*t command
	# 			except ValueError:
	# 				self.sendMessage(chat_id=chat_id,
	# 					text="Unknown command!"
	# 					)
	#
	# 		# Updates global offset to get the new updates
	# 		self.LAST_UPDATE_ID = update.update_id + 1
	#



def main():
	MainPicSender(BOT_TOKEN)

if __name__ == '__main__':
	main()