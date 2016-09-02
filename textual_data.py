#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
from os import path

SCRIPT_FOLDER = path.dirname(path.realpath(__file__))

# from settings_reader import SettingsReader
# sr = SettingsReader()

##############
# FILENAMES###
##############

# Databases containing user parameters, file info and other stuff are located here
# DATABASES_FOLDER_NAME="databases"

# A file containing a link to the public folder
DROPBOX_FOLDER_LINK_FILENAME = "links/DB_public_link"

# Filename of database containing user data
# USERS_DB_FILENAME = "users"

#A link to shared folder on Dropbox
with open(path.join(SCRIPT_FOLDER,DROPBOX_FOLDER_LINK_FILENAME), 'r') as f:
	DROPBOX_FOLDER_LINK= f.read().split("\n")[0]

#File storing dropbox keys
DROPBOX_TOKEN_FILENAME="tokens/dropbox_tokens"

#Dropbox app keys
with open(path.join(SCRIPT_FOLDER, DROPBOX_TOKEN_FILENAME),'r') as f:
	DROPBOX_APP_KEY,DROPBOX_SECRET_KEY = f.read().split("\n")[:2]

#A filename of a file containing Telegram bot token.
BOT_TOKEN_FILENAME = 'tokens/token'

with open(path.join(SCRIPT_FOLDER, BOT_TOKEN_FILENAME),'r') as f:
	BOT_TOKEN = f.read().replace("\n","")

#A name of a file containing metadata which is displayed together with a picture.
METADATA_FILENAME = "pic_bot_meta.txt"

#A path where subscribers list is saved.
# SUBSCRIBERS_BACKUP_FILE = '/tmp/picbot_subscribers_bak'

# Local folder containing pictures
# PIC_FOLDER = sr.settings_reader(3)

# Folder containing pictures in Dropbox
DROPBOX_PIC_FOLDER = "/"

#############
# TEXTS######
#############

START_MESSAGE = "Welcome! Type /help to get help."

################
### BUTTONS#####
################

ABOUT_BUTTON = "ℹ️ About"
HELP_BUTTON = "⁉️" + "Help"
OTHER_BOTS_BUTTON = "👾 My other bots"
GIMMEPIC_BUTTON = '🎢' + "Gimme Pic!"
SUBSCRIBE_BUTTON = '✏️' + "Subscribe"
UNSUBSCRIBE_BUTTON = '🚫' + "Unsubscribe"
SHOW_PERIOD_BUTTON = "⏲" + "Show period"

##############
### MESSAGES##
##############

ALREADY_SUBSCRIBED_MESSAGE = """You have already subscribed!
To cancel subscription enter /unsubscribe.
To change the period of picture sending type a number.
Your current period is {0} seconds."""

SUBSCRIBED_MESSAGE = """You're subscribed now!
An image will be sent to you every {0} seconds.
To cancel subscription enter /unsubscribe.
To change the period of picture sending type a number."""

NOT_SUBSCRIBED_YET_MESSAGE = "You haven't subscribed yet! To subscribe type /subscribe"

UNSUBSCRIBED_MESSAGE = "You have unsubscribed. To subscribe again type /subscribe"

##################
# BIG TEXTS#######
##################

ABOUT_MESSAGE = """*Random Picture Bot*
_Created by:_ Highstaker a.k.a. OmniSable.
Source: https://github.com/Highstaker/Picture-sender-telegram-bot
Version: {0}
This bot uses the python-telegram-bot library.
https://github.com/leandrotoledo/python-telegram-bot
"""

HELP_MESSAGE = '''
This bot sends you random pictures from its collection.
To get a random picture, type /gimmePic.
To make this bot send you a random picture every set amount of time (by default it is
	{0} seconds) type /subscribe.
To set a period of sending (in seconds), type a number.
+ Minimum: {1} seconds.
+ Maximum: {2} seconds.
To stop receiving pictures, type /unsubscribe
'''

OTHER_BOTS_MESSAGE = """*My other bots*:

@OmniCurrencyExchangeBot: a currency converter bot supporting past rates and graphs.

@multitran\_bot: a Russian-Whichever dictionary with support of 9 languages. Has transcriptions for English words.
"""

UNKNOWN_COMMAND_MESSAGE = "Unknown command"

