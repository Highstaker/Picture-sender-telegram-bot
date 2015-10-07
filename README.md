#Random Picture Sender bot for Telegram

##Overview

This bot sends a random picture from a specified folder (subfolders included) to a subscribed user once in a fixed period of time. A user can change the period by typing a number. Additionally, a user may request a random picture right away.

##Deployment

To use this program create a file called "token" in the script's folder and paste your bot's token into it (you can call the file otherwise by modifying the TOKEN_FILENAME variable). Then change the FOLDER variable to represent the path to your picture folder.

##Dependencies

This program relies on python-telegram-bot.
https://github.com/leandrotoledo/python-telegram-bot

To install it, use:
pip install python-telegram-bot