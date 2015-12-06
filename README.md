#Random Picture Sender bot for Telegram

##Overview

This bot sends a random picture from a specified folder (subfolders included) to a subscribed user once in a fixed period of time. A user can change the period by typing a number. Additionally, a user may request a random picture right away.

##Deployment

To use this program create a file called "token" in the script's folder and paste your bot's token into it (you can call the file otherwise by modifying the `TOKEN_FILENAME` variable). Change `SUBSCRIBERS_BACKUP_FILE` to a path to a file that will be a backup for subscribers list (This is done to prevent loss of subscribers list if a bot crashes and restarts).

If you want to use files on your local filesystem, set `FROM_DROPBOX` to `False`.Then change the `FOLDER` variable to represent the path to your picture folder.

Set `FROM_DROPBOX` to `True` to make the bot grab pictures from a public folder in Dropbox. Create an app with full Dropbox permissions in your Dropbox settings. Create a file with a name specified in `DROPBOX_TOKEN_FILENAME` variable and paste your app key and secret key into it, on separate lines (token is not needed, this bot will not be able to modify your Dropbox storage's contents). Then create a file named as in `DROPBOX_FOLDER_LINK_FILENAME` variable and paste a link to a public Dropbox folder containing your images into it.

You may create a text file in a folder containing pictures (its name is specified by `METADATA_FILENAME` variable) with a text that will be shown together with a picture (for example, Authors of a drawing or photo, etc.).

##Dependencies

This program uses **Python 3**

This program relies on [python-telegram-bot](https://github.com/leandrotoledo/python-telegram-bot).

To install it, use:
`pip3 install python-telegram-bot`