#!/usr/bin/python3 -u
#TODO
#+Add help
#+Add upper limit of period
#+fix freezing on connection loss (the bot won't reconnect even if connection is restored)

import logging
import telegram
from os import path, listdir, walk
from random import choice
from time import time
from itertools import chain
import socket

#if a connection is lost and getUpdates takes too long, an error is raised
socket.setdefaulttimeout(30)

# logging.basicConfig(level = logging.DEBUG)

logging.basicConfig(format = u'[%(asctime)s] %(filename)s[LINE:%(lineno)d]# %(levelname)-8s  %(message)s', 
	level = logging.WARNING)


############
##PARAMETERS
############

HELP_MESSAGE = '''
Help message.
'''

with open(path.join(path.dirname(path.realpath(__file__)), 'token'),'r') as f:
	BOT_TOKEN = f.read().replace("\n","")

KEY_MARKUP = [["/subscribe","/unsubscribe","/gimmePic","/help"]]

FOLDER = path.join(path.expanduser("~"), 'pic_bot_pics')

#A minimum and maximum picture sending period a user can set
MIN_PICTURE_SEND_PERIOD = 30
MAX_PICTURE_SEND_PERIOD = 86400

#A default send period
PICTURE_SEND_PERIOD = 600
# PICTURE_SEND_PERIOD = 5#debug

################
###GLOBALS
############


#############
##METHODS###
############

def get_filepaths_incl_subfolders(FOLDER):
	myFolder = FOLDER
	fileSet = set() 

	for root, dirs, files in walk(myFolder,followlinks=True):
		for fileName in files:
			fileSet.add( path.join( root, fileName ))
	return list(fileSet)

class TelegramBot():
	"""docstring for TelegramBot"""

	LAST_UPDATE_ID = None

	#{chat_id: [waiting_time_between_image_sendings,time of the last image sending], ...}
	subscribers = {}

	def __init__(self, token):
		super(TelegramBot, self).__init__()
		self.bot = telegram.Bot(token)
		#get list of all image files
		self.files = get_filepaths_incl_subfolders(FOLDER)

	def sendMessage(self,chat_id,text):
		logging.warning("Replying to " + str(chat_id) + " " + text)
		while True:
			try:
				self.bot.sendMessage(chat_id=chat_id,
					text=text,
					reply_markup=telegram.ReplyKeyboardMarkup(KEY_MARKUP)
					)
			except telegram.error.TelegramError:
				logging.error("Could not send message. Retrying!")
				continue
			break

	def sendPic(self,chat_id,pic):
		logging.warning("Sending image to " + str(chat_id) + " " + str(pic))
		while True:
			try:
				logging.debug("Picture: " + str(pic))
				#set file read cursor to the beginning. This ensures that if a file needs to be re-read (may happen due to exception), it is read from the beginning.
				pic.seek(0)
				self.bot.sendPhoto(chat_id=chat_id,photo=pic)
			except telegram.error.TelegramError as e:
				logging.error("Could not send picture. Retrying! Error: " + str(e))
				continue
			break

	def sendRandomPic(self,chat_id):
		with open( choice( self.files ),"rb" ) as pic:
			logging.warning("Sending image to " + str(chat_id) + " " + str(pic))
			self.sendPic(chat_id,pic)


	def echo(self):
		bot = self.bot

		for i in self.subscribers:
			if (time() - self.subscribers[i][1]) > self.subscribers[i][0]:
				self.sendRandomPic(i)
				self.subscribers[i][1] = time()

		#if getting updates fails - retry
		while True:
			try:
				updates = bot.getUpdates(offset=self.LAST_UPDATE_ID, timeout=3)
			except telegram.error.TelegramError:
				logging.error("Could not read updates. Retrying!")
				continue
			break

		for update in updates:
			chat_id = update.message.chat_id
			Message = update.message
			from_user = Message.from_user
			message = Message.text
			logging.warning("Received message: " + str(chat_id) + " " + from_user.username + " " + message)

			if message == "/subscribe":
				if not chat_id in self.subscribers:
					self.subscribers[chat_id] = [PICTURE_SEND_PERIOD,time()]
					self.sendMessage(chat_id=chat_id,
						text="You're now subscribed. To cancel subscription enter /unsubscribe. To change the period of picture sending type a number.",
						)
				else:
					self.sendMessage(chat_id=chat_id,
						text="You have already subscribed. To cancel subscription enter /unsubscribe. To change the period of picture sending type a number.",
						)
			elif message == "/help":
				self.sendMessage(chat_id=chat_id
					,text=HELP_MESSAGE
					)
			elif message == "/unsubscribe":
				try:
					del self.subscribers[chat_id]
					self.sendMessage(chat_id=chat_id,
						text="You have unsubscribed. To subscribe again type /subscribe",
						)
				except KeyError:
					self.sendMessage(chat_id=chat_id,
						text="You are not on the list, there is nowhere to unsubscribe you from. To subscribe type /subscribe",
						)
			elif message == "/gimmePic":
				self.sendRandomPic(chat_id)
			else:
				try:
					self.subscribers[chat_id]#check if user has subscribed
					new_period = int(message)
					if new_period < MIN_PICTURE_SEND_PERIOD:
						self.subscribers[chat_id][0] = MIN_PICTURE_SEND_PERIOD
						self.sendMessage(chat_id=chat_id,
							text="The minimum possible period is " + str(MIN_PICTURE_SEND_PERIOD) + ".\nSetting period to " + str(MIN_PICTURE_SEND_PERIOD) + "."
							)
						self.subscribers[chat_id][1] = time()
					elif new_period > MAX_PICTURE_SEND_PERIOD:
						self.subscribers[chat_id][0] = MAX_PICTURE_SEND_PERIOD
						self.sendMessage(chat_id=chat_id,
							text="The maximum possible period is " + str(MAX_PICTURE_SEND_PERIOD) + ".\nSetting period to " + str(MAX_PICTURE_SEND_PERIOD) + "."
							)
						self.subscribers[chat_id][1] = time()
					else:
						self.subscribers[chat_id][0] = new_period
						self.sendMessage(chat_id=chat_id,
							text="Setting period to " + str(new_period) + "."
							)
						self.subscribers[chat_id][1] = time()

				#user not in list, not subscribed
				except KeyError:
					self.sendMessage(chat_id=chat_id,
						text="You're not subscribed yet! /subscribe first!"
						)

				#user has sent a bullsh*t command
				except ValueError:
					self.sendMessage(chat_id=chat_id,
						text="unknown command"
						)

			# Updates global offset to get the new updates
			self.LAST_UPDATE_ID = update.update_id + 1


def main():
	bot = TelegramBot(BOT_TOKEN)

	while True:
		bot.echo()

if __name__ == '__main__':
	main()