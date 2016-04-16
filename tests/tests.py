#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
import unittest
from os import path
import sys

# The folder containing the script itself
SCRIPT_FOLDER = path.dirname(path.realpath(__file__))

# Needed to add folder above to look for modules
sys.path.append(path.dirname(SCRIPT_FOLDER))
print("sys.path",sys.path)

from textual_data import *

# A flag. If set to True, runs the tests that use Telegram
USER_TEST = False

# A flag. If set to True, the tests that require user's participation are run
USER_INTERACTION_TEST = False

# A flag. Runs Dropbox tests if True
DROPBOX_TEST = False

import utils

class UtilsStringConversionUtilsTest(unittest.TestCase):

	def test_isInt(self):
		isInt = utils.StringConversionUtils.isInt

		self.assertTrue(isInt("0"))
		self.assertTrue(isInt("-1"))
		self.assertTrue(isInt("42"))
		self.assertFalse(isInt("qweradg213r"))
		self.assertFalse(isInt("4.2"))

class UtilsDictUtilsTest(unittest.TestCase):
	#############
	## replaceKey()
	#############
	def test_replaceKey(self):
		dic = dict(a="Hello", b="Hola!")
		utils.DictUtils.replaceKey(dic,"a","c")
		self.assertEqual(dic, {"c":"Hello", "b": "Hola!"})

	def test_replaceKey_to_same(self):
		dic = dict(a="Hello", b="Hola!")
		utils.DictUtils.replaceKey(dic,"a","a")
		self.assertEqual(dic, {"a":"Hello", "b": "Hola!"})

	def test_replaceKey_to_other_type(self):
		dic = dict(a="Hello", b="Hola!")
		utils.DictUtils.replaceKey(dic,"a",1)
		self.assertEqual(dic, {1:"Hello", "b": "Hola!"})
		utils.DictUtils.replaceKey(dic,"b",3.5)
		self.assertEqual(dic, {1:"Hello", 3.5: "Hola!"})
		utils.DictUtils.replaceKey(dic,3.5,"zz")
		self.assertEqual(dic, {1:"Hello", "zz": "Hola!"})

	def test_replace_nonexisting_key(self):
		dic = dict(a="Hello", b="Hola!")
		# I have to pass lambda, because the function is evaluated before assertRaises,
		# and therefore does not represent how it should be.
		# http://stackoverflow.com/a/6103930/2052138
		self.assertRaises(KeyError, lambda: utils.DictUtils.replaceKey(dic,"x","z"))

	#############
	## dictGetCaseInsensitive
	#############

	def test_dictGetCaseInsensitive_with_asis(self):
		dic = dict(Aa="Hello!", bB="Hola!")
		self.assertEqual(utils.DictUtils.dictGetCaseInsensitive(dic,"Aa"),"Hello!")
		self.assertEqual(utils.DictUtils.dictGetCaseInsensitive(dic,"bB"),"Hola!")

	def test_dictGetCaseInsensitive_with_other_case(self):
		dic = dict(Aa="Hello!", bB="Hola!")
		self.assertEqual(utils.DictUtils.dictGetCaseInsensitive(dic,"aa"),"Hello!")
		self.assertEqual(utils.DictUtils.dictGetCaseInsensitive(dic,"bb"),"Hola!")
		self.assertEqual(utils.DictUtils.dictGetCaseInsensitive(dic,"AA"),"Hello!")
		self.assertEqual(utils.DictUtils.dictGetCaseInsensitive(dic,"BB"),"Hola!")
		self.assertEqual(utils.DictUtils.dictGetCaseInsensitive(dic,"aA"),"Hello!")
		self.assertEqual(utils.DictUtils.dictGetCaseInsensitive(dic,"Bb"),"Hola!")

	def test_dictGetCaseInsensitive_with_nonexisting_key(self):
		dic = dict(Aa="Hello!", bB="Hola!")
		self.assertRaises(KeyError, lambda: utils.DictUtils.dictGetCaseInsensitive(dic,"CC"))

	def test_dictGetCaseInsensitive_with_nonexisting_nonstring_key(self):
		dic = dict(Aa="Hello!", bB="Hola!")
		self.assertRaises(KeyError, lambda: utils.DictUtils.dictGetCaseInsensitive(dic,42))

	def test_dictGetCaseInsensitive_with_existing_nonstring_key(self):
		dic = dict(Aa="Hello!", bB="Hola!")
		dic.update({42:"Guten Tag!", 3.5: "Привет!"})
		self.assertEqual(utils.DictUtils.dictGetCaseInsensitive(dic, 42),"Guten Tag!")
		self.assertEqual(utils.DictUtils.dictGetCaseInsensitive(dic, 3.5),"Привет!")

class UtilsFolderSearchTest(unittest.TestCase):

	def test_getFilepathsInclSubfolders(self):
		func_files = utils.FolderSearch.getFilepathsInclSubfolders(path.join(SCRIPT_FOLDER, "test_pics"))
		print(func_files)
		files = ["test_pics/pic1.png", "test_pics/pic2.jpeg", "test_pics/pic3.jpg", "test_pics/002/pic4.jpg"]
		files = [path.join(path.abspath(SCRIPT_FOLDER), i) for i in files]

		self.assertEqual(len(func_files), 5)

		for i in files:
			self.assertIn(i,func_files)

	def test_getFilepathsInclSubfolders_empty(self):
		func_files = utils.FolderSearch.getFilepathsInclSubfolders(path.join(SCRIPT_FOLDER, "test_pics/empty_dir"))
		self.assertEqual(len(func_files), 0)
		self.assertEqual(func_files, [])

	def test_getFilepathsInclSubfolders_filtered(self):
		files_in = ["test_pics/pic1.png", "test_pics/pic2.jpeg"]
		files_in = [path.join(path.abspath(SCRIPT_FOLDER), i) for i in files_in]

		files_not_in = ["test_pics/pic3.jpg", "test_pics/002/pic4.jpg"]
		files_not_in = [path.join(path.abspath(SCRIPT_FOLDER), i) for i in files_not_in]

		func_files = utils.FolderSearch.getFilepathsInclSubfolders(path.join(SCRIPT_FOLDER, "test_pics"),
																   allowed_extensions=['jpeg','PNG'])
		self.assertEqual(len(func_files), 2)

		for i in files_in:
			self.assertIn(i, func_files)

		for i in files_not_in:
			self.assertNotIn(i, func_files)

class UtilsDropboxFolderSearchTest(unittest.TestCase):

	def __init__(self,dunno):
		super(UtilsDropboxFolderSearchTest, self).__init__(dunno)

		with open(path.join(path.dirname(SCRIPT_FOLDER), DROPBOX_TOKEN_FILENAME), 'r')as f:
			data = f.read().split("\n")
			self.DROPBOX_APP_KEY = data[0]
			self.DROPBOX_SECRET_KEY = data[1]

		with open(path.join(path.dirname(SCRIPT_FOLDER), DROPBOX_FOLDER_LINK_FILENAME), 'r')as f:
			data = f.read().split("\n")
			self.DB_LINK = data[0]

	def test_DropboxFolderSearch(self):
		if DROPBOX_TEST:
			dfs = utils.DropboxFolderSearch.getFilepathsInclSubfoldersDropboxPublic(
				self.DB_LINK,
				self.DROPBOX_APP_KEY,
				self.DROPBOX_SECRET_KEY
				)
			print("dfs", dfs)
			self.assertTrue(dfs)


from language_support import LanguageSupport
class LanguageSupportTest(unittest.TestCase):

	def test_language_support_with_string(self):
		message = "Test message!!!1111"
		lang = "en"
		L = LanguageSupport(lang)
		self.assertEqual(L.languageSupport(message), message)

	def test_language_support_with_string_no_lang(self):
		message = "Test message!!!1111"
		lang = ""
		L = LanguageSupport(lang)
		self.assertEqual(L.languageSupport(message), message)

	def test_language_support_with_dict(self):
		message = {"EN": "Test message!!!1111", "ES": "¡El Texto!"}
		lang = "EN"
		L = LanguageSupport(lang)
		self.assertEqual(L.languageSupport(message), message["EN"])
		lang = "ES"
		L = LanguageSupport(lang)
		self.assertEqual(L.languageSupport(message), message["ES"])
		#Try nonexisting language. Should default to English
		lang = "DE"
		L = LanguageSupport(lang)
		self.assertEqual(L.languageSupport(message), message["EN"])

	def test_language_support_with_dict_varied_language_case(self):
		message = {"eN": "Test message!!!1111", "es": "¡El Texto!", "Ru": "Текст для проверки"}
		lang = "en"
		L = LanguageSupport(lang)
		self.assertEqual(L.languageSupport(message), message["eN"])
		lang = "ES"
		L = LanguageSupport(lang)
		self.assertEqual(L.languageSupport(message), message["es"])
		lang = "RU"
		L = LanguageSupport(lang)
		self.assertEqual(L.languageSupport(message), message["Ru"])
		#Try nonexisting language. Should default to English
		lang = "DE"
		L = LanguageSupport(lang)
		self.assertEqual(L.languageSupport(message), message["eN"])

	def test_language_support_with_dict_without_english_and_nonexisting_language(self):
		message = {"es": "¡El Texto!", "Ru": "Текст для проверки"}
		lang = "DE"
		L = LanguageSupport(lang)
		self.assertRaises(KeyError, lambda: L.languageSupport(message))

	def test_all_variants_string(self):
		message = "Hello"
		lang = "DE"
		L = LanguageSupport(lang)
		self.assertEqual(L.allVariants(message), [message])

	def test_all_variants_dict(self):
		message = {"eN": "Test message!!!1111", "es": "¡El Texto!", "Ru": "Текст для проверки"}
		L = LanguageSupport
		a = list(message.values())
		b = L.allVariants(message)
		self.assertEqual(sorted(a),sorted(b))

	def test_all_variants_empty_dict(self):
		message = dict()
		L = LanguageSupport
		a = []
		b = L.allVariants(message)
		self.assertEqual(sorted(a),sorted(b))

	def test_all_variants_other_types(self):
		L = LanguageSupport
		a = []
		message = 42
		b = L.allVariants(message)
		self.assertEqual(sorted(a),sorted(b))
		message = 3.5
		b = L.allVariants(message)
		self.assertEqual(sorted(a),sorted(b))
		message = ['a',1]
		b = L.allVariants(message)
		self.assertEqual(sorted(a),sorted(b))
		message = ('a',1,)
		b = L.allVariants(message)
		self.assertEqual(sorted(a),sorted(b))


from telegramHigh import TelegramHigh
class TelegramHighTest(unittest.TestCase):

	# def __init__(self):
		# super().__init__()
	@classmethod
	def setUpClass(cls):
		with open(path.join(SCRIPT_FOLDER, "tests/testbot_token"), "r") as f:
			cls.BOT_TOKEN = f.read()

		with open(path.join(SCRIPT_FOLDER, "tests/testbot_chatid"), "r") as f:
			cls.chat_id = f.read()  # chat_id for you


	def test_breakLongMessage_short_message(self):
		bot = TelegramHigh
		message = "abc\nxyz"
		self.assertEqual(TelegramHigh.breakLongMessage(message),[message])

	def test_breakLongMessage_long_message_with_newlines(self):
		bot = TelegramHigh
		message = "0"*600 + "\n" + "1"*1800 +'\n'+ "abcde" + '\n' + "42"*100
		self.assertEqual(TelegramHigh.breakLongMessage(message),["0"*600, "1"*1800+"\nabcde\n"+"42"*100])

	def test_breakLongMessage_long_message_with_bigchunk_no_newlines(self):
		bot = TelegramHigh
		message = "0"*10000
		broken = TelegramHigh.breakLongMessage(message)
		self.assertEqual(len(broken), 5)
		self.assertEqual(len(broken[0]), 2048)
		self.assertEqual(broken[0], "0"*2048)
		self.assertEqual(len(broken[1]), 2048)
		self.assertEqual(len(broken[2]), 2048)
		self.assertEqual(len(broken[3]), 2048)
		self.assertEqual(len(broken[4]), 1808)
		self.assertEqual(broken[4], "0"*1808)
		self.assertEqual(broken,["0"*2048,"0"*2048,"0"*2048,"0"*2048,"0"*1808])

	def test_breakLongMessage_long_message_with_bigchunks_and_newlines(self):
		bot = TelegramHigh
		message = "0"*3000 + '\n' + "1"*1000 + '\n' + "2"*2100 + '\n' + "abcde"
		broken = TelegramHigh.breakLongMessage(message)
		self.assertEqual(len(broken), 6)
		self.assertEqual(len(broken[0]), 2048)
		self.assertEqual(broken[0], "0"*2048)
		self.assertEqual(len(broken[1]), 952)
		self.assertEqual(len(broken[2]), 1000)
		self.assertEqual(len(broken[3]), 2048)
		self.assertEqual(len(broken[4]), 52)
		self.assertEqual(len(broken[5]), 5)
		self.assertEqual(broken,["0"*2048, "0"*952, "1"*1000, "2"*2048, "2"*52, "abcde"])

	def test_sendMessage(self):
		if USER_TEST:
			bot = TelegramHigh(self.BOT_TOKEN)
			bot.sendMessage(self.chat_id, "abcde")

	def test_sendMessage_big(self):
		if USER_TEST:
			bot = TelegramHigh(self.BOT_TOKEN)
			bot.sendMessage(self.chat_id, "0"*10000)

	def test_sendMessage_markdown(self):
		if USER_TEST:
			bot = TelegramHigh(self.BOT_TOKEN)
			bot.sendMessage(self.chat_id, "hello\nNice to*meet* you! 8", markdown=True)
			bot.sendMessage(self.chat_id, "hello\nNice to_meet_ you! 8", markdown=True)
			bot.sendMessage(self.chat_id, "hello\nNice to`meet` you! 8", markdown=True)
			bot.sendMessage(self.chat_id, "hello\nNice to[meet](ya.ru) you! 8", markdown=True)

	def test_sendMessage_broken_markdown(self):
		if USER_TEST:
			bot = TelegramHigh(self.BOT_TOKEN)
			bot.sendMessage(self.chat_id, "hello\nNice to*meet you! 8", markdown=True)
			bot.sendMessage(self.chat_id, "hello\nNice to_meet you! 8", markdown=True)
			bot.sendMessage(self.chat_id, "hello\nNice to`meet you! 8", markdown=True)
			bot.sendMessage(self.chat_id, "hello\nNice to[meet() you! 8", markdown=True)

	def test_sendPic_files(self):
		if USER_TEST:
			bot = TelegramHigh(self.BOT_TOKEN)
			bot.sendPic(chat_id=self.chat_id, pic=open("test_pics/002/pic4.jpg", 'rb'), caption="")
			bot.sendPic(chat_id=self.chat_id, pic=open("test_pics/pic3.jpg", 'rb'), caption="")
			bot.sendPic(chat_id=self.chat_id, pic=open("test_pics/pic2.jpeg", 'rb'))
			bot.sendPic(chat_id=self.chat_id, pic=open("test_pics/pic1.png", 'rb'), caption="Test png")

	def test_sendPic_bytestring(self):
		if USER_TEST:
			data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\t\x08\x06\x00\x00\x00;*\xac2\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\x00\x00\tpHYs\x00\x00\x0e\xc4\x00\x00\x0e\xc4\x01\x95+\x0e\x1b\x00\x00\x01GIDAT(\x91}\x8f\xdd+Cq\x00\x86\x9fs\xce\xef\x9c\xb1\x8f\xc8W[\x8b|m$\x85\xb8 R\x96\x92r\xad\x94\x0bW\xfe\x00\xca5\xe5/\x10\xd7\xca\xe5R\xca\x8d\x9a"\x97\x92\xdd\x90\x88\xb5\x93\xc6i\x8b\xadm\x92a\xfb\xb9\xb2\xc8\x99\xf7\xfa}\x9e\xb7W\x91RJl"\xa5\xe4\xad\xf0N$z\xcc\xd1\xd9\x01\xd7V\x1c\xa3\x94gin\x85\x89\x81\xe9rO\xb5\x83\xbf\x93\xcc\xa489\xdf\xe5"yN\xb6x\xcbP\xcf \xa3\xbd\x93\xbf:\xc2\x0e\xcc\xe5\xd2\xa0\xea\\\x997\xc4\xccG\n)\x8b6\x7f\x13\xcb\xb3\xab\x18\xba^Y \xa5$z\xb8O8\xbc\xc5\xa7(b\x15\xd2h\x1f\x02\xcd]\xcb`\xfb\x08n\xa7\xfb\xcf\x98\xf8\tG\xf66\t\xefo\x90\xd5t\x94\xa7w\xbc5\xcdx\xfa\xfay\x91\x19fB\x0b\xb67\xcb\x82\xd8]\x94\xc8\xf6:\x0fU\x02\xf2:\x9e\xfa\x1a\xa6\xe6W\xf0\xfbZ\xe8\xe9\x08`\x08\xddV\xa0\x02\xdc^\x9e\xb2\xb3\xb6\x88\x99+Q\xf7\xf4A\xde%\xd0\xdf$\x1eW5\xdd\xad\x9d\x18BGQ\x94\xca\x82\xd7\x84E\xd6L\x12DAkw\x91\xc3KF:)Ip8\x8c\x8apY\x10\x18\x0b\xd15<\x8e\xda\xe0\xa0\x18/\x11L\'\xf0\xdd?\xe3\xafkD\xfd\x07\x06\xf8\x02Wcq9\xe1\r \xc0\x00\x00\x00\x00IEND\xaeB`\x82'
			bot = TelegramHigh(self.BOT_TOKEN)
			bot.sendPic(chat_id=self.chat_id, pic=data)

	def test_sendPic_bad_object(self):
		if USER_TEST:
			bot = TelegramHigh(self.BOT_TOKEN)
			#string
			bot.sendPic(chat_id=self.chat_id, pic="test_pics/pic1.jpg", caption="")
			#none
			bot.sendPic(chat_id=self.chat_id, pic=None)
			#Nonexisting file
			self.assertRaises(FileNotFoundError, lambda:
							  bot.sendPic(chat_id=self.chat_id,
										  pic=open("test_pics/ppppp.jpg", 'rb'), caption="lol"))

	def test_sendPic_badFileID(self):
		if USER_TEST:
			bot = TelegramHigh(self.BOT_TOKEN)

			self.assertRaisesRegex(Exception,
			"Network error",
			lambda:
			bot.sendPic(chat_id=self.chat_id, pic="AgADAgADvKwxG-wJf1qMovYCa4r-r-nVgioABJAQ_xRgcmsrHhoCAAEC")
							)

			self.assertRaisesRegex(Exception,
			"Network error",
			lambda:
			bot.sendPic(chat_id=self.chat_id, pic="AgADAgADvKwxG-wJf1qMova4r-r-nVgioABJAQ_xRgcmsrHhoCAAEC")
							)

	def awaitUpdates(self, bot):
		"""
		Waits for an update and returns the latest one
		:param bot:
		:return:
		"""
		#Flush existing updates
		try:
			u = bot.bot.getUpdates()[-1]
			bot.bot.getUpdates(offset=u.update_id + 1)
		except IndexError:
			pass

		while True:
			u = bot.getUpdates()
			print("update list",u)
			if u:
				break
		return u[-1]

	def test_isPhoto(self):
		if USER_INTERACTION_TEST:
			bot = TelegramHigh(self.BOT_TOKEN)
			bot.sendMessage(self.chat_id, "Send a *photo*!", markdown=True)
			self.assertTrue(bot.isPhoto(self.awaitUpdates(bot)))
			bot.sendMessage(self.chat_id, "Send a *file*!", markdown=True)
			self.assertFalse(bot.isPhoto(self.awaitUpdates(bot)))
			bot.sendMessage(self.chat_id, "Send a *message*!", markdown=True)
			self.assertFalse(bot.isPhoto(self.awaitUpdates(bot)))

	def test_isDocument(self):
		if USER_INTERACTION_TEST:
			bot = TelegramHigh(self.BOT_TOKEN)
			bot.sendMessage(self.chat_id, "Send a *photo*!", markdown=True)
			self.assertFalse(bot.isDocument(self.awaitUpdates(bot)))
			bot.sendMessage(self.chat_id, "Send a *file*!", markdown=True)
			self.assertTrue(bot.isDocument(self.awaitUpdates(bot)))
			bot.sendMessage(self.chat_id, "Send a *message*!", markdown=True)
			self.assertFalse(bot.isDocument(self.awaitUpdates(bot)))


if __name__ == "__main__":
	unittest.main()