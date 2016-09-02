#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
from sys import exit
from os import path
from logging_handler import LoggingHandler
log = LoggingHandler(__name__)

SCRIPT_FOLDER = path.dirname(path.realpath(__file__))


class SettingsReader:
	"""docstring for SettingsReader"""
	_instance = None
	_inited = False

	def __new__(cls, *args, **kwargs):
		# SINGLETON
		if cls._instance is None:
			cls._instance = super(SettingsReader, cls).__new__(cls)
			cls._inited = False
		return cls._instance

	def __init__(self):
		if not self._inited:
			super(SettingsReader, self).__init__()

			self.settings = self.processSettings(self.readSettingsFile())

			self._inited = True

	def __getitem__(self, item):
		return self.settings_reader()[item]

	@staticmethod
	def readSettingsFile():
		settings = ""
		try:
			with open(path.join(SCRIPT_FOLDER, "settings/settings.txt"), 'r') as f:
				settings = f.read()
		except FileNotFoundError:
			log.error("Settings file not found! Aborting!")
			exit(1)
		return settings

	@staticmethod
	def checkValidity(settings):
		s = settings["picture_send_period"]
		if not isinstance(s, int) or s <= 0:
			log.error("PICTURE_SEND_PERIOD invalid! It should be a positive integer! Aborting!")
			exit(1)
		s = settings["file_update_period"]
		if not isinstance(s, int) or s <= 0:
			log.error("FILE_UPDATE_PERIOD invalid! It should be a positive integer! Aborting!")
			exit(1)
		s = settings["pic_source"]
		if s not in ('local', 'DB',):
			log.error("FILE_UPDATE_PERIOD invalid! It should be either 'local' or 'DB'! Aborting!")
			exit(1)

		return True

	def processSettings(self, settings):
		# noinspection PyPep8Naming
		# names of fields in settings file, for more convenient access via dictionary
		SETTING_NAMES = ("file_update_period", "picture_send_period", "pic_source", "pic_folder",)

		settings = settings.split("\n")
		result = dict()
		for n, set_name in enumerate(SETTING_NAMES):
			setting = settings[n].split("##")[0].strip(" \n\r\t")
			try:
				# if a setting is a number, try making it an integer
				setting = int(setting)
			except ValueError:
				pass
			result[set_name] = setting

		self.checkValidity(result)

		return result

	def settings_reader(self):
		return self.settings

if __name__ == '__main__':
	sr = SettingsReader()
	print(sr.settings_reader())
	print('pic_folder', sr['pic_folder'])
	print('file_update_period', sr['file_update_period'])
	print('picture_send_period', sr['picture_send_period'])
	print('pic_source', sr['pic_source'])

	sr2 = SettingsReader()

	print(sr is sr2)
