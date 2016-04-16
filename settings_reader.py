#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
from sys import exit
from os import path
from logging_handler import LoggingHandler as Lh

SCRIPT_FOLDER = path.dirname(path.realpath(__file__))


class SettingsReader:
	"""docstring for SettingsReader"""
	instance = None

	def __new__(cls, *args, **kwargs):
		if cls.instance == None:
			cls.instance = super(SettingsReader, cls).__new__(cls)
		return cls.instance


	def __init__(self):
		super(SettingsReader, self).__init__()
		try:
			with open(path.join(SCRIPT_FOLDER,"settings/settings.txt"), 'r') as f:
				self.settings = f.read()
		except FileNotFoundError:
			Lh.error("Settings file not found! Aborting!")
			exit(1)

		self.processSettings()

	def processSettings(self):
		self.settings = self.settings.split("\n")
		for n,i in enumerate(self.settings):
			self.settings[n] = i.split("#")[0].strip(" \n\r\t")
			try:
				self.settings[n] = int(self.settings[n])
			except ValueError:
				pass

	def settings_reader(self, index):
		return self.settings[index]

if __name__ == '__main__':
	sr = SettingsReader()
	for i in range(4):
		print(sr.settings_reader(i), type(sr.settings_reader(i)))