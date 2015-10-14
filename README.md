#Random Picture Sender bot for Telegram

##Overview

This bot sends a random picture from a specified folder (subfolders included) to a subscribed user once in a fixed period of time. A user can change the period by typing a number. Additionally, a user may request a random picture right away.

##Deployment

To use this program create a file called "token" in the script's folder and paste your bot's token into it (you can call the file otherwise by modifying the `TOKEN_FILENAME` variable). Then change the `FOLDER` variable to represent the path to your picture folder. Change `SUBSCRIBERS_BACKUP_FILE` to a path to a file that will be a backup for subscribers list (This is done to prevent loss of subscribers list if a bot crashes and restarts).

##Dependencies

This program uses **Python 3**

This program relies on [python-telegram-bot](https://github.com/leandrotoledo/python-telegram-bot).

To install it, use:
`pip3 install python-telegram-bot`