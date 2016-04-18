#Random Picture Sender bot for Telegram

##Overview

This bot sends a random picture from a specified folder (subfolders included) to a subscribed user once in a fixed period of time. A user can change the period by typing a number. Additionally, a user may request a random picture right away.

##Deployment

###Requirements

This program was written and tested in **Python 3.4.3**. Make sure your version is up-to-date.

This program's installation script relies on `virtualenv` to install the environment suitable for the bot. 
If you don't have it instlled, run `sudo pip3 install virtualenv`.

###Installing the bot

Clone the repo to your installation directory, then run `setup.sh`. This should install the required Python libraries.

In `tokens` folder, paste your bot's token (received from BotFather) into `token` file.
Adjust the `settings.txt` file in `settings` folder to meet your requirements (explanations are present in the file).

If you use _Dropbox_, put your app key and app secret key on first two lines in `dropbox_tokens` file in `tokens` directory. Dropbox app token is not needed, only app keys (See your Dropbox app settings).
Additionally, create a public link to a Dropbox folder containing your images and put this link into `DB_public_link` file in `links` folder.

###Running the bot

Run `run.sh` to start the bot.

##Dependencies

This program uses **Python 3.4.3**

The bot relies on [python-telegram-bot](https://github.com/leandrotoledo/python-telegram-bot).

All requirements shall be installed with `setup.sh` script.

##Tested operating systems.

* Ubuntu 14.04 Desktop
* Ubuntu 14.04 Server
