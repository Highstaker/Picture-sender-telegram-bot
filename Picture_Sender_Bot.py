#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

VERSION_NUMBER = (0,7,0)

import logging
import telegram
from os import path, listdir, walk
from random import choice
from time import time
from itertools import chain
import socket
import pickle #module for saving dictionaries to file

#if a connection is lost and getUpdates takes too long, an error is raised
socket.setdefaulttimeout(30)

logging.basicConfig(format = u'[%(asctime)s] %(filename)s[LINE:%(lineno)d]# %(levelname)-8s  %(message)s', 
	level = logging.WARNING)


############
##PARAMETERS
############

#A filename of a file containing a token.
TOKEN_FILENAME = 'token'

#A name of a file containing metadata which is displayed together with a picture.
METADATA_FILENAME = "pic_bot_meta.txt"

#A path where subscribers list is saved.
SUBSCRIBERS_BACKUP_FILE = '/tmp/picbot_subscribers_bak'

#folder containing pictures
FOLDER = path.join(path.expanduser("~"), 'pic_bot_pics')

#A minimum and maximum picture sending period a user can set
MIN_PICTURE_SEND_PERIOD = 30
MAX_PICTURE_SEND_PERIOD = 86400

#A default send period
PICTURE_SEND_PERIOD = 600
# PICTURE_SEND_PERIOD = 5#debug

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

ABOUT_BUTTON = "ℹ️ About"
HELP_BUTTON = "⁉️" + "Help"
GIMMEPIC_BUTTON = '🎢' + "Gimme Pic!"
SUBSCRIBE_BUTTON = '✏️' + "Subscribe"
UNSUBSCRIBE_BUTTON = '🚫' + "Unsubscribe"
KEY_MARKUP = [[SUBSCRIBE_BUTTON,UNSUBSCRIBE_BUTTON],[GIMMEPIC_BUTTON],[ HELP_BUTTON, ABOUT_BUTTON]]

################
###GLOBALS######
################

with open(path.join(path.dirname(path.realpath(__file__)), TOKEN_FILENAME),'r') as f:
	BOT_TOKEN = f.read().replace("\n","")



#############
##METHODS###
############

def get_filepaths_incl_subfolders(FOLDER):
	"""
	Returns a list of full paths to all files in a folder and subfolders. Follows links! 
	"""
	myFolder = FOLDER
	fileSet = set() 

	for root, dirs, files in walk(myFolder,followlinks=True):
		for fileName in files:
			fileSet.add( path.join( root, fileName ))
	return list(fileSet)

###############
###CLASSES#####
###############

class TelegramBot():
	"""The bot class"""

	LAST_UPDATE_ID = None

	#{chat_id: [waiting_time_between_image_sendings,time of the last image sending], ...}
	subscribers = {}

	def __init__(self, token):
		super(TelegramBot, self).__init__()
		self.bot = telegram.Bot(token)
		#get list of all image files
		self.files = get_filepaths_incl_subfolders(FOLDER)
		self.loadSubscribers()

	def loadSubscribers(self):
		'''
		Loads subscribers from a file
		'''
		try:
			with open(SUBSCRIBERS_BACKUP_FILE,'rb') as f:
				self.subscribers = pickle.load(f)
				print("self.subscribers",self.subscribers)
		except FileNotFoundError:
			logging.warning("Subscribers backup file not found. Starting with empty list!")

	def saveSubscribers(self):
		'''
		Saves a subscribers list to file
		'''
		with open(SUBSCRIBERS_BACKUP_FILE,'wb') as f:
			pickle.dump(self.subscribers, f, pickle.HIGHEST_PROTOCOL)

	def sendMessage(self,chat_id,text):
		logging.warning("Replying to " + str(chat_id) + ": " + text)
		while True:
			try:
				self.bot.sendChatAction(chat_id,telegram.ChatAction.TYPING)
				self.bot.sendMessage(chat_id=chat_id,
					text=text,
					parse_mode='Markdown',
					reply_markup=telegram.ReplyKeyboardMarkup(KEY_MARKUP)
					)
			except Exception as e:
				logging.error("Could not send message. Retrying! Error: " + str(e))
				continue
			break

	def sendPic(self,chat_id,pic):
		while True:
			try:
				logging.debug("Picture: " + str(pic))
				self.bot.sendChatAction(chat_id,telegram.ChatAction.UPLOAD_PHOTO)
				#set file read cursor to the beginning. This ensures that if a file needs to be re-read (may happen due to exception), it is read from the beginning.
				pic.seek(0)
				self.bot.sendPhoto(chat_id=chat_id,photo=pic)
			except Exception as e:
				logging.error("Could not send picture. Retrying! Error: " + str(e))
				continue
			break

	def sendRandomPic(self,chat_id):
		random_pic_path = choice( self.files )
		with open( random_pic_path,"rb" ) as pic:
			logging.warning("Sending image to " + str(chat_id) + " " + str(pic))
			self.sendPic(chat_id,pic)

		#try sending metadata if present. Skip if not.
		try:
			with open( path.join( path.abspath(path.join(random_pic_path, path.pardir)), METADATA_FILENAME), "r") as metafile:
				self.sendMessage(chat_id=chat_id,
					text=metafile.read()
					)
		except FileNotFoundError:
			pass


	def echo(self):
		bot = self.bot

		#check if it is time to send an image already
		for i in self.subscribers:
			if (time() - self.subscribers[i][1]) > self.subscribers[i][0]:
				#The time has come for this user
				self.sendRandomPic(i)
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
			elif message == "/subscribe" or message == SUBSCRIBE_BUTTON:
				if not chat_id in self.subscribers:
					self.subscribers[chat_id] = [PICTURE_SEND_PERIOD,time()]
					self.saveSubscribers()
					self.sendMessage(chat_id=chat_id,
						text="You're now subscribed. The default period of image sending is " + str(PICTURE_SEND_PERIOD) + " seconds. To cancel subscription enter /unsubscribe. To change the period of picture sending type a number.",
						)
				else:
					self.sendMessage(chat_id=chat_id,
						text="You have already subscribed. To cancel subscription enter /unsubscribe. To change the period of picture sending type a number.",
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
				self.sendRandomPic(chat_id)
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