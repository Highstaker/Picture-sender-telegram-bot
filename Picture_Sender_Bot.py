#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
#TODO

VERSION_NUMBER = (0, 9, 8)

import logging
import telegram
from os import path, listdir, walk, remove as file_remove
from random import choice
from time import time,sleep
from itertools import chain
import socket
import pickle #module for saving dictionaries to file
import requests, json
from multiprocessing import Process, Queue

#if a connection is lost and getUpdates takes too long, an error is raised
socket.setdefaulttimeout(30)

logging.basicConfig(format = u'[%(asctime)s] %(filename)s[LINE:%(lineno)d]# %(levelname)-8s  %(message)s', 
	level = logging.WARNING)


############
##PARAMETERS
############

#How often should a file list of images be updated
FILE_UPDATE_PERIOD = 86400

#If true, use dropbox. If false, use local filesystem
FROM_DROPBOX = True

#A file containing a link to the public folder
DROPBOX_FOLDER_LINK_FILENAME = "DB_public_link"

#A link to shared folder on Dropbox
with open(path.join(path.dirname(path.realpath(__file__)),DROPBOX_FOLDER_LINK_FILENAME), 'r') as f:
	DROPBOX_FOLDER_LINK= f.read().split("\n")[0]

#File storing dropbox keys
DROPBOX_TOKEN_FILENAME="dropbox_tokens"

#Dropbox app keys
with open(path.join(path.dirname(path.realpath(__file__)), DROPBOX_TOKEN_FILENAME),'r') as f:
	DROPBOX_APP_KEY,DROPBOX_SECRET_KEY = f.read().split("\n")[:2]

#A filename of a file containing a token.
TOKEN_FILENAME = 'token'

#A name of a file containing metadata which is displayed together with a picture.
METADATA_FILENAME = "pic_bot_meta.txt"

#A path where subscribers list is saved.
SUBSCRIBERS_BACKUP_FILE = '/tmp/picbot_subscribers_bak'

#folder containing pictures
FOLDER = path.join(path.expanduser("~"), 'pic_bot_pics')

#folder containing pictures in Dropbox
DROPBOX_FOLDER = "/Изображения/Inspiration_folder"

#A minimum and maximum picture sending period a user can set
MIN_PICTURE_SEND_PERIOD = 60
MAX_PICTURE_SEND_PERIOD = 86400

#A default send period
PICTURE_SEND_PERIOD = 600

ABOUT_MESSAGE = """*Random Picture Bot*
_Created by:_ Highstaker a.k.a. OmniSable.
Source: https://github.com/Highstaker/Picture-sender-telegram-bot
Version: """ + ".".join([str(i) for i in VERSION_NUMBER]) + """
This bot uses the python-telegram-bot library.
https://github.com/leandrotoledo/python-telegram-bot
"""

HELP_MESSAGE = '''
This bot sends you random pictures from its collection.
To get a random picture, type /gimmePic.
''' \
+ "To make this bot send you a random picture every set amount of time (by default it is " \
+ str(PICTURE_SEND_PERIOD) + " seconds) type /subscribe." \
+'''
To set a period of sending (in seconds), type a number.
''' \
+ "Minimum: " + str(MIN_PICTURE_SEND_PERIOD) + " seconds.\n" \
+ "Maximum: " + str(MAX_PICTURE_SEND_PERIOD) + " seconds.\n" \
+ '''
To stop receiving pictures, type /unsubscribe
'''

START_MESSAGE = "Welcome! Type /help to get help."

OTHER_BOTS_MESSAGE = """*My other bots*:

@OmniCurrencyExchangeBot: a currency converter bot supporting past rates and graphs.

@multitran\_bot: a Russian-Whichever dictionary with support of 9 languages. Has transcriptions for English words.
"""

ABOUT_BUTTON = "ℹ️ About"
HELP_BUTTON = "⁉️" + "Help"
GIMMEPIC_BUTTON = '🎢' + "Gimme Pic!"
SUBSCRIBE_BUTTON = '✏️' + "Subscribe"
UNSUBSCRIBE_BUTTON = '🚫' + "Unsubscribe"
OTHER_BOTS_BUTTON = "👾 My other bots"

MAIN_MENU_KEY_MARKUP = [
[SUBSCRIBE_BUTTON,UNSUBSCRIBE_BUTTON],
[GIMMEPIC_BUTTON],
[HELP_BUTTON, ABOUT_BUTTON, OTHER_BOTS_BUTTON]
]

################
###GLOBALS######
################

with open(path.join(path.dirname(path.realpath(__file__)), TOKEN_FILENAME),'r') as f:
	BOT_TOKEN = f.read().replace("\n","")



#############
##METHODS###
############

def getFilepathsInclSubfolders(FOLDER):
	"""
	Returns a list of full paths to all files in a folder and subfolders. Follows links! 
	"""
	myFolder = FOLDER
	fileSet = set() 

	for root, dirs, files in walk(myFolder,followlinks=True):
		for fileName in files:
			fileSet.add( path.join( root, fileName ))
	return list(fileSet)

def getFilepathsInclSubfoldersDropboxPublic(LINK):
	'''
	Returns a list of full paths to all files in a public folder (provided with a link) and subfolders in Dropbox 
	'''

	def readDir(LINK,DIR):
		#Set a loop to retry connection if it is refused
		result = []
		while True:
			try:
				req=requests.post('https://api.dropbox.com/1/metadata/link',data=dict( link=LINK, client_id=DROPBOX_APP_KEY,client_secret=DROPBOX_SECRET_KEY, path=DIR) )

				for i in json.loads(req.content.decode())['contents']:
					if i['is_dir']:
						logging.warning("Reading directory: " + str(i['path']))#debug
						result += readDir(LINK,i['path'])
					else:
						#a file, add to list
						result += [i['path']]

				break
			except:
				sleep(60)#wait a bit before retrying
				pass

		return result

	filelist = readDir(LINK,"/")

	return filelist

###############
###CLASSES#####
###############

class TelegramBot():
	"""The bot class"""

	LAST_UPDATE_ID = None

	#{chat_id: [waiting_time_between_image_sendings,time of the last image sending], ...}
	subscribers = {}

	#Dictionary containing hanndles to picture-sending processes
	processes = {}

	#once dropbox user is authorized, set to true to allow operations
	DB_authorized = False

	#the moment when the file list was last updated
	last_update_time=time()

	def __init__(self, token):
		super(TelegramBot, self).__init__()
		self.bot = telegram.Bot(token)

		self.loadSubscribers()

		#get list of all image files
		self.updateFileList()

	def updateFileList(self):
		'''
		Reads the files in the directory and updates the file list
		'''
		self.files = getFilepathsInclSubfolders(FOLDER) if not FROM_DROPBOX else getFilepathsInclSubfoldersDropboxPublic(DROPBOX_FOLDER_LINK)
		self.last_update_time=time()

	def languageSupport(self,chat_id,message):
		'''
		Returns a message depending on a language chosen by user
		'''
		if isinstance(message,str):
			result = message
		elif isinstance(message,dict):
			try:
				result = message[self.subscribers[chat_id][0]]
			except:
				result = message["EN"]
		elif isinstance(message,list):
			#could be a key markup
			result = list(message)
			for n,i in enumerate(message):
				result[n] = self.languageSupport(chat_id,i)
		else:
			result = " "
			
		return result


	def loadSubscribers(self):
		'''
		Loads subscribers from a file
		'''
		try:
			with open(SUBSCRIBERS_BACKUP_FILE,'rb') as f:
				self.subscribers = pickle.load(f)
				logging.warning(("self.subscribers",self.subscribers))
		except FileNotFoundError:
			logging.warning("Subscribers backup file not found. Starting with empty list!")

	def saveSubscribers(self):
		'''
		Saves a subscribers list to file
		'''
		with open(SUBSCRIBERS_BACKUP_FILE,'wb') as f:
			pickle.dump(self.subscribers, f, pickle.HIGHEST_PROTOCOL)

	def sendMessage(self,chat_id,text,key_markup=MAIN_MENU_KEY_MARKUP,preview=True):
		logging.warning("Replying to " + str(chat_id) + ": " + text)
		key_markup = self.languageSupport(chat_id,key_markup)
		while True:
			try:
				if text:
					self.bot.sendChatAction(chat_id,telegram.ChatAction.TYPING)
					self.bot.sendMessage(chat_id=chat_id,
						text=text,
						parse_mode='Markdown',
						disable_web_page_preview=(not preview),
						reply_markup=telegram.ReplyKeyboardMarkup(key_markup, resize_keyboard=True)
						)
			except Exception as e:
				if "Message is too long" in str(e):
					self.sendMessage(chat_id=chat_id
						,text="Error: Message is too long!"
						)
					break
				if ("urlopen error" in str(e)) or ("timed out" in str(e)):
					logging.error("Could not send message. Retrying! Error: " + str(e))
					sleep(3)
					continue
				else:
					logging.error("Could not send message. Error: " + str(e))
			break

	def sendPic(self,chat_id,pic,caption=None):
		while True:
			try:
				logging.debug("Picture: " + str(pic))
				self.bot.sendChatAction(chat_id,telegram.ChatAction.UPLOAD_PHOTO)
				#set file read cursor to the beginning. This ensures that if a file needs to be re-read (may happen due to exception), it is read from the beginning.
				pic.seek(0)
				self.bot.sendPhoto(chat_id=chat_id,photo=pic,caption=caption)
			except Exception as e:
				if ("urlopen error" in str(e)) or ("timed out" in str(e)):
					logging.error("Could not send message. Retrying! Error: " + str(e))
					sleep(3)
					continue
				elif "IncompleteRead" in str(e):
					logging.error("IncompleteRead error. Retrying!" + str(e))
					sleep(1)
					continue
				else:
					logging.error("Could not send message. Error: " + str(e))
			break

	def sendPicProcess(self,chat_id,pic,caption=None):
		self.sendPic(chat_id=chat_id,pic=pic,caption=caption)

	def sendRandomPic(self,chat_id,queue):
		if not FROM_DROPBOX:
			###########
			###from local filesystem
			##############
			random_pic_path = ""
			while not (path.splitext(random_pic_path)[1].lower() in ['.jpg', '.jpeg', '.gif', '.png', '.tif', '.bmp']):
				#filtering. Only images should be picked
				random_pic_path = choice( self.files )
			metadata=""
			#try sending metadata if present. Skip if not.
			try:
				with open( path.join( path.abspath(path.join(random_pic_path, path.pardir)), METADATA_FILENAME), "r") as metafile:
					metadata=metafile.read()
			except FileNotFoundError:
				pass

			with open( random_pic_path,"rb" ) as pic:
				logging.warning("Sending image to " + str(chat_id) + " " + str(pic))
				self.sendPic(chat_id,pic,caption=metadata)


		else:
			############
			#from dropbox
			###########
			while True:
				random_pic_path = ""
				while not (path.splitext(random_pic_path)[1].lower() in ['.jpg', '.jpeg', '.gif', '.png', '.tif', '.bmp']):
					#filtering. Only images should be picked
					random_pic_path = choice( self.files )
					tmp_path = path.join("/tmp/", path.basename(random_pic_path) )
				#First, get metadata of a file. It contains a direct link to it!
				req=requests.post('https://api.dropbox.com/1/metadata/link',data=dict( link=DROPBOX_FOLDER_LINK, client_id=DROPBOX_APP_KEY,client_secret=DROPBOX_SECRET_KEY, path=random_pic_path), timeout=10 )
				if req.ok:
					#If metadata got grabbed, extract a link to a file and make a downloadable version of it
					req= json.loads(req.content.decode())['link'].split("?")[0] + "?dl=1"
					#now let's get the file contents
					try:
						req=requests.get(req,timeout=30)
						if req.ok:
							req= req.content
							break
					except:
						pass

				else:
					#handle absence of file (maybe got deleted?)
					pass

			metadata=""
			#try to read metadata
			try:
				meta_req=requests.post('https://api.dropbox.com/1/metadata/link',data=dict( link=DROPBOX_FOLDER_LINK, client_id=DROPBOX_APP_KEY,client_secret=DROPBOX_SECRET_KEY, path=path.join(path.dirname(random_pic_path),METADATA_FILENAME ) ) , timeout=10)
				if meta_req.ok:
						meta_req= json.loads(meta_req.content.decode())['link'].split("?")[0] + "?dl=1"
						meta_req = requests.get(meta_req,timeout=10)
						metadata = meta_req.content.decode()
				else:
					metadata=""
			except:
				metadata=""
				pass

			with open(tmp_path, 'wb') as tmppic:
				#now let's save the file to temporary
				tmppic.write(req)

			with open(tmp_path, 'rb') as pic:
				#send the file
				
				for att in range(3):
					logging.warning("Attempt " + str(att+1) + " of sending image to " + str(chat_id) + " " + str(pic))
					p = Process(target=self.sendPicProcess,args=(chat_id,pic,metadata,))
					p.start()

					#wait 5 seconds then repeat attempt. Exit loop if process has terminated.
					startTime = time()
					while time() - startTime < 5:
						if not p.is_alive():
							break

					if not p.is_alive():
						break
					else:
						p.terminate()
				else:
					self.sendMessage(chat_id=chat_id,text="Failed to send picture. Please try again!")

			# delete temporary file
			file_remove(tmp_path)


	def echo(self):
		bot = self.bot

		def startRandomPicProcess(chat_id):
			'''
			Starts and image sending process.
			'''
			def startProcess():
				q = Queue()
				p = Process(target=self.sendRandomPic,args=(chat_id,q,))
				self.processes[chat_id]=(p,q)
				p.start()
			try:
				if self.processes[chat_id][0].is_alive():
					#the process is still working
					self.sendMessage(chat_id=chat_id
						,text="I'm still sending you a picture. Please wait!"
						)
				else:
					#the process entry exists but the process is terminated. Very improbable.
					startProcess()
			except KeyError:
				startProcess()

		#clean the image-getting processes that have terminated
		tempProcesses=dict(self.processes) #because error occurs if dictionary changes size during loop
		for i in tempProcesses:
			if not self.processes[i][0].is_alive():
				del self.processes[i]

		#check if it is time to update the file list
		if time() - self.last_update_time > FILE_UPDATE_PERIOD:
			self.updateFileList()

		#check if it is time to send an image already
		for i in self.subscribers:
			if (time() - self.subscribers[i][1]) > self.subscribers[i][0]:
				#The time has come for this user (heh, sounds intimidating)
				startRandomPicProcess(i)
				#Reset user's timer
				self.subscribers[i][1] = time()
				#Save to file
				self.saveSubscribers()

		#if getting updates fails - retry
		while True:
			try:
				updates = bot.getUpdates(offset=self.LAST_UPDATE_ID, timeout=3)
			except Exception as e:
				logging.error("Could not read updates. Retrying! Error: " + str(e))
				continue
			break

		for update in updates:
			chat_id = update.message.chat_id
			Message = update.message
			from_user = Message.from_user
			message = Message.text
			logging.warning("Received message: " + str(chat_id) + " " + from_user.username + " " + message)

			if message == "/start":
				self.sendMessage(chat_id=chat_id
					,text=START_MESSAGE
					)
			elif message == "/help" or message == HELP_BUTTON:
				self.sendMessage(chat_id=chat_id
					,text=HELP_MESSAGE
					)
			elif message == "/about" or message == ABOUT_BUTTON:
				self.sendMessage(chat_id=chat_id
					,text=ABOUT_MESSAGE
					)
			elif message == "/otherbots" or message == self.languageSupport(chat_id,OTHER_BOTS_BUTTON):
				self.sendMessage(chat_id=chat_id
					,text=self.languageSupport(chat_id,OTHER_BOTS_MESSAGE)
					)
			elif message == "/subscribe" or message == SUBSCRIBE_BUTTON:
				if not chat_id in self.subscribers:
					self.subscribers[chat_id] = [PICTURE_SEND_PERIOD,time()]
					self.saveSubscribers()
					self.sendMessage(chat_id=chat_id,
						text="You're now subscribed. The default period of image sending is " + str(PICTURE_SEND_PERIOD) + " seconds. To cancel subscription enter /unsubscribe. To change the period of picture sending type a number.",
						)
				else:
					self.sendMessage(chat_id=chat_id,
						text="You have already subscribed. To cancel subscription enter /unsubscribe. To change the period of picture sending type a number.\nYour current period is " + str(self.subscribers[chat_id][0])+ " seconds.",
						)
			elif message == "/unsubscribe" or message == UNSUBSCRIBE_BUTTON:
				try:
					del self.subscribers[chat_id]
					self.saveSubscribers()
					self.sendMessage(chat_id=chat_id,
						text="You have unsubscribed. To subscribe again type /subscribe",
						)
				except KeyError:
					self.sendMessage(chat_id=chat_id,
						text="You are not on the list, there is nowhere to unsubscribe you from. To subscribe type /subscribe",
						)
			elif message == "/gimmepic" or message == GIMMEPIC_BUTTON:
				startRandomPicProcess(chat_id)
			else:
				#any other message
				try:
					self.subscribers[chat_id]#check if user has subscribed
					new_period = int(message)

					#If a period is too small
					if new_period < MIN_PICTURE_SEND_PERIOD:
						self.subscribers[chat_id][0] = MIN_PICTURE_SEND_PERIOD
						self.sendMessage(chat_id=chat_id,
							text="The minimum possible period is " + str(MIN_PICTURE_SEND_PERIOD) + ".\nSetting period to " + str(MIN_PICTURE_SEND_PERIOD) + "."
							)
						self.subscribers[chat_id][1] = time()

					#If a period is too big
					elif new_period > MAX_PICTURE_SEND_PERIOD:
						self.subscribers[chat_id][0] = MAX_PICTURE_SEND_PERIOD
						self.sendMessage(chat_id=chat_id,
							text="The maximum possible period is " + str(MAX_PICTURE_SEND_PERIOD) + ".\nSetting period to " + str(MAX_PICTURE_SEND_PERIOD) + "."
							)
						self.subscribers[chat_id][1] = time()

					#If a period length is fine - accept
					else:
						self.subscribers[chat_id][0] = new_period
						self.sendMessage(chat_id=chat_id,
							text="Setting period to " + str(new_period) + "."
							)
						self.subscribers[chat_id][1] = time()

					#A new period should be saved to file
					self.saveSubscribers()

				#user not in list, not subscribed
				except KeyError:
					self.sendMessage(chat_id=chat_id,
						text="You're not subscribed yet! /subscribe first!"
						)

				#user has sent a bullsh*t command
				except ValueError:
					self.sendMessage(chat_id=chat_id,
						text="Unknown command!"
						)

			# Updates global offset to get the new updates
			self.LAST_UPDATE_ID = update.update_id + 1


def main():
	bot = TelegramBot(BOT_TOKEN)

	#main loop
	while True:
		bot.echo()

if __name__ == '__main__':
	main()