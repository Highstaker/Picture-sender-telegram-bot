#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

from textual_data import *

# class ButtonHandler(object):
# 	"""docstring for ButtonHandler"""
#
# 	instance = None
#
# 	def __new__(cls):
# 		#singleton
# 		if cls.instance is None:
# 			cls.instance = super(ButtonHandler, cls).__new__(cls)
# 		return cls.instance
#
# 	def __init__(self):
# 		super(ButtonHandler, self).__init__()
#
# 	@staticmethod
def getMainMenu(subscribed):
	"""
	Returns a representation of custom keyboard to be passed to message-sending functions
	:param subscribed: is the user subscribed?
	Affects which button shall be displayed, subscribe or unsubscribe
	:return: list of lists
	"""

	subscribe_button = [UNSUBSCRIBE_BUTTON, SHOW_PERIOD_BUTTON] if subscribed else [SUBSCRIBE_BUTTON]

	MAIN_MENU_KEY_MARKUP = [
	subscribe_button,
	[GIMMEPIC_BUTTON],
	[HELP_BUTTON, ABOUT_BUTTON, OTHER_BOTS_BUTTON]
	]

	return MAIN_MENU_KEY_MARKUP