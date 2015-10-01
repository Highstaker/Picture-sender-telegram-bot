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

PICTURE_SEND_PERIOD = 60 * 5
# PICTURE_SEND_PERIOD = 1#debug

################
###GLOBALS
############


#############
##METHODS###
############

class TelegramBot():
	"""docstring for TelegramBot"""

	LAST_UPDATE_ID = None

	subscribers = []

	def __init__(self, token):
		super(TelegramBot, self).__init__()
		self.bot = telegram.Bot(token)
		self.start_time = time()

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



		if (time() - self.start_time) > PICTURE_SEND_PERIOD:
			debug('sending images')
			#create a flattened list of files from all FOLDERS
			# files = list(chain.from_iterable( [[path.join(j,i) for i in listdir(j) if path.isfile(path.join(j,i))] for j in FOLDERS] ) )
			files = get_filepaths_incl_subfolders(FOLDER)
			for i in self.subscribers:
				with open( choice( files ),"rb" ) as pic:
					bot.sendPhoto(chat_id=i,photo=pic)
			self.start_time = time()

		updates = bot.getUpdates(offset=self.LAST_UPDATE_ID, timeout=3)

		for update in updates:
			chat_id = update.message.chat_id
			Message = update.message
			message = Message.text

			if message == "/subscribe":
				if not chat_id in self.subscribers:
					self.subscribers += [chat_id]
					self.sendMessage(chat_id=chat_id,
						text="You're now subscribed. To cancel subscription enter /unsubscribe",
						)
				else:
					self.sendMessage(chat_id=chat_id,
						text="You have already subscribed. To cancel subscription enter /unsubscribe",
						)
			elif message == "/unsubscribe":
				try:
					del self.subscribers[self.subscribers.index(chat_id)]
					self.sendMessage(chat_id=chat_id,
						text="You have unsubscribed. To subscribe again type /subscribe",
						)
				except ValueError:
					self.sendMessage(chat_id=chat_id,
						text="You are not on the list, there is nowhere to unsubscribe you from. To subscribe type /subscribe",
						)
			else:
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