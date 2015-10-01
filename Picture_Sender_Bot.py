#!/usr/bin/python3

import telegram
from os import path, listdir, walk
from random import choice
from time import time
from itertools import chain

DEBUG = True
def debug(*msg):
	if DEBUG:
		print('[DEBUG]', msg)

############
##PARAMETERS
############

BOT_TOKEN = "124973178:AAEN9yweYlGdqGpCrfoTyINfNqzIW5cGf10"

KEY_MARKUP = [["/subscribe","/unsubscribe"]]

# FOLDERS = ["Изображения/Bluari","Изображения/Allen Williams", "Изображения/AlectorFencer", "Изображения/Bengtern", "Изображения/Nimrais", "Изображения/Psychonautic", "Изображения/Peter Williams","Изображения/Maquenda","Изображения/Rhyu","Изображения/Inspiration_folder/3D","Изображения/Naira","Изображения/BubbleWolf","Изображения/ShadowWolf","Изображения/Tatchit","Изображения/DarkNatasha"]
# FOLDERS = [path.join(path.expanduser("~"), i) for i in FOLDERS]
FOLDER = path.join(path.expanduser("~"), 'pic_bot_pics')

#A minimum picture sending period a user can set
MIN_PICTURE_SEND_PERIOD = 5

PICTURE_SEND_PERIOD = 60 * 5
# PICTURE_SEND_PERIOD = 5#debug

################
###GLOBALS
############


#############
##METHODS###
############

class TelegramBot():
	"""docstring for TelegramBot"""

	LAST_UPDATE_ID = None

	#{chat_id: [waiting_time_between_image_sendings,time of the last image sending], ...}
	subscribers = {}

	def __init__(self, token):
		super(TelegramBot, self).__init__()
		self.bot = telegram.Bot(token)
		# self.start_time = time()

	def sendMessage(self,chat_id,text):
		self.bot.sendMessage(chat_id=chat_id,
						text=text,
						reply_markup=telegram.ReplyKeyboardMarkup(KEY_MARKUP)
						)

	def echo(self):
		bot = self.bot

		def get_filepaths_incl_subfolders(FOLDER):
			myFolder = FOLDER
			fileSet = set() 

			for root, dirs, files in walk(myFolder,followlinks=True):
				for fileName in files:
					fileSet.add( path.join( root, fileName ))
			return list(fileSet)

		files = get_filepaths_incl_subfolders(FOLDER)

		for i in self.subscribers:
			debug('sending images')

			if (time() - self.subscribers[i][1]) > self.subscribers[i][0]:
				with open( choice( files ),"rb" ) as pic:
					bot.sendPhoto(chat_id=i,photo=pic)
				self.subscribers[i][1] = time()

		updates = bot.getUpdates(offset=self.LAST_UPDATE_ID, timeout=3)

		for update in updates:
			chat_id = update.message.chat_id
			Message = update.message
			message = Message.text

			if message == "/subscribe":
				if not chat_id in self.subscribers:
					self.subscribers[chat_id] = [PICTURE_SEND_PERIOD,time()]
					self.sendMessage(chat_id=chat_id,
						text="You're now subscribed. To cancel subscription enter /unsubscribe",
						)
				else:
					self.sendMessage(chat_id=chat_id,
						text="You have already subscribed. To cancel subscription enter /unsubscribe",
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