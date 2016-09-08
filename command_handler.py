from telegram.ext import CommandHandler, MessageHandler, Filters, Job, JobQueue

from VERSION import VERSION_NUMBER
from textual_data import *
from picbot_routines import PicBotRoutines
from language_support import LanguageSupport
from database_handler import time

from dropbox_handler import DropboxHandler
from settings_reader import SettingsReader
from logging_handler import LoggingHandler
sr = SettingsReader()
log = LoggingHandler(__name__, max_level="DEBUG")

MIN_PICTURE_SEND_PERIOD = 60
MAX_PICTURE_SEND_PERIOD = 86400

LOCAL_CLEANER_PERIOD = 3600

subscriptions_tasks = dict()


class UserCommandHandler(PicBotRoutines):
	"""docstring for UserCommandHandler"""

	def _command_method(func):
		"""Decorator for functions that are invoked on commands. Ensures that the user is initialized."""

		# @functools.wraps(func)
		def wrapper(self, bot, update, *args, **kwargs):
			# print("command method", func.__name__, )  # debug
			# print("self",self)# debug
			# print("command method", self, bot, update, args, kwargs, sep="||")  # debug
			chat_id = update.message.chat_id

			log.info("Command method called!", func.__name__, "Chat_id: ", chat_id)

			# Initialize user, if not present in DB
			self.database_handler.initializeUser(chat_id=chat_id)
			log.debug("User initialized")

			lS = LanguageSupport(self.database_handler.getLang(chat_id)).languageSupport

			# noinspection PyCallingNonCallable
			func(self, bot, update, lS)

			log.debug("Function completed")

		return wrapper

	def __init__(self, bot, dispatcher, database_handler, token):

		self.dispatcher = dispatcher

		# queue for async jobs
		self.job_queue = JobQueue(bot)

		# Where to get pictures from: local filesystem(local) or Dropbox storage (DB)
		self.pic_source = sr["pic_source"]

		self.database_handler = database_handler

		super(UserCommandHandler, self).__init__(token, self.database_handler)

		self._addHandlers()

		if self.pic_source == "DB":
			self.DB_file_updater_thread = None # a thread that updates files
			self.dropbox_handler = DropboxHandler(self.database_handler)
			self._updateDBFiles()
		elif self.pic_source == "local":
			self.local_cleaner_job = None
			self._startLocalCleanerJob()

		self._initializeSubscriptionJobs()

	def _initializeSubscriptionJobs(self):
		for chat_id in self.database_handler.getAllSubscribedUserIDs():
			log.debug("_initializeSubscriptionJobs chat_id", chat_id)
			self.createPeriodicSenderTask(chat_id)

	def _updateDBFiles(self, bot=None, job=None):
		if not self.DB_file_updater_thread or not self.DB_file_updater_thread.is_alive():
			self.DB_file_updater_thread = self.dropbox_handler.updateFiles()
			job = Job(self._updateDBFiles, interval=sr['file_update_period'], repeat=False)
		else:
			log.warning("The Dropbox updater thread hasn't finished yet. Consider increasing FILE_UPDATE_PERIOD in settings!")
			job = Job(self._updateDBFiles, interval=10, repeat=False)

		# create periodic job
		self.job_queue.put(job)

	def _startLocalCleanerJob(self):
		"""
		Creates a delayed async job that cleans database every now and then if local files get deeleted
		:return:
		"""
		log.debug("_startLocalCleanerJob")
		self.local_cleaner_job = job = Job(self._localCleanerThread, interval=LOCAL_CLEANER_PERIOD, repeat=True)
		self.job_queue.put(job)

	def _localCleanerThread(self, bot, job):
		log.debug("_localCleanerThread")
		local_files = self.getLocalFiles()
		bd_files = set(self.database_handler.getFileList())
		to_delete = bd_files.difference(local_files)
		log.debug("to_delete", to_delete)

		if to_delete:
			self.database_handler.batchDeleteFiles(to_delete)


	def _addHandlers(self):
		self.dispatcher.add_handler(CommandHandler('start', self.command_start))
		self.dispatcher.add_handler(CommandHandler('help', self.command_help))
		self.dispatcher.add_handler(CommandHandler('about', self.command_about))
		self.dispatcher.add_handler(CommandHandler('otherbots', self.command_otherbots))
		self.dispatcher.add_handler(CommandHandler('gimmepic', self.command_gimmepic))
		self.dispatcher.add_handler(CommandHandler('subscribe', self.command_subscribe))
		self.dispatcher.add_handler(CommandHandler('unsubscribe', self.command_unsubscribe))
		self.dispatcher.add_handler(CommandHandler('spamuncached', self.command_spamuncached))



		# non-command message
		self.dispatcher.add_handler(MessageHandler([Filters.text], self.messageMethod))

		# unknown commands
		self.dispatcher.add_handler(MessageHandler([Filters.command], self.unknown_command))

		self.dispatcher.add_error_handler(self.error_handler)

		log.info("Commands set!")

	def setPeriod(self, bot, update, lS=None):
		message = update.message.text
		chat_id = update.message.chat_id

		try:
			new_period = int(message)

			if not self.database_handler.getSubscribed(chat_id):
				self.sendMessageCommandMethod(bot, update, "You're not subscribed yet! /subscribe first!")
			else:
				# If a period is too small
				if new_period < MIN_PICTURE_SEND_PERIOD:
					self.database_handler.setPeriod(chat_id, MIN_PICTURE_SEND_PERIOD)
					self.sendMessageCommandMethod(bot, update,
												  "The minimum possible period is {0}.\nSetting period to {0}.".format(
										str(MIN_PICTURE_SEND_PERIOD)))

				# If a period is too big
				elif new_period > MAX_PICTURE_SEND_PERIOD:
					self.database_handler.setPeriod(chat_id, MAX_PICTURE_SEND_PERIOD)
					self.sendMessageCommandMethod(bot, update,
									"The maximum possible period is {0}.\nSetting period to {0}.".format(
										str(MAX_PICTURE_SEND_PERIOD)))

				# If a period length is fine - accept
				else:
					self.database_handler.setPeriod(chat_id, new_period)
					self.sendMessageCommandMethod(bot, update,
									"Setting period to {0}.".format(new_period)
									)

				# Reset timer
				self.database_handler.resetTimer(chat_id)
				self.restartPeriodicTask(chat_id)

			return True

		# user has sent a bullsh*t command
		except ValueError:
			return False

	def doGimmepic(self, chat_id):
		if self.pic_source == "local":
			self.sendLocalRandomPic(chat_id)
		elif self.pic_source == "DB":
			self.sendDropboxRandomPic(chat_id)

	def _periodicSender(self, bot, job):
		chat_id = job.context
		self.doGimmepic(chat_id)
		self.database_handler.resetTimer(chat_id)
		self.restartPeriodicTask(chat_id)

	def restartPeriodicTask(self, chat_id):
		self.removePeriodicSenderTask(chat_id)
		self.createPeriodicSenderTask(chat_id)

	def createPeriodicSenderTask(self, chat_id):
		time_left = self.database_handler.getSendTime(chat_id) - time()
		log.debug("Time left:", time_left)

		job = Job(self._periodicSender, time_left, context=chat_id)
		subscriptions_tasks[chat_id] = job
		self.job_queue.put(job)

	def removePeriodicSenderTask(self, chat_id):
		subscriptions_tasks[chat_id].schedule_removal()  # remove task from job queue
		del subscriptions_tasks[chat_id]


	##########
	# COMMAND METHODS
	##########

	# GENERIC COMMANDS

	# noinspection PyArgumentList
	@_command_method
	def command_start(self, bot, update, lS=None):
		self.sendMessageCommandMethod(bot, update, lS(START_MESSAGE))

	# noinspection PyArgumentList
	@_command_method
	def command_help(self, bot, update, lS=None):
		msg = lS(HELP_MESSAGE).format(sr['picture_send_period'],MIN_PICTURE_SEND_PERIOD, MAX_PICTURE_SEND_PERIOD)
		self.sendMessageCommandMethod(bot, update, msg)

	# noinspection PyArgumentList
	@_command_method
	def command_about(self, bot, update, lS=None):
		msg = lS(ABOUT_MESSAGE).format(".".join([str(i) for i in VERSION_NUMBER]))
		self.sendMessageCommandMethod(bot, update, msg, disable_web_page_preview=False)

	# noinspection PyArgumentList
	# @_command_method
	def command_otherbots(self, bot, update, lS=None):
		# a = 2/0
		self.sendMessageCommandMethod(bot, update, OTHER_BOTS_MESSAGE)

	# noinspection PyArgumentList
	@_command_method
	def messageMethod(self, bot, update, lS=None):
		chat_id = update.message.chat_id
		message = update.message.text

		log.info("messageMethod. Chat_id:", chat_id, "Message:", message)

		if message in LanguageSupport.allVariants(HELP_BUTTON):
			self.command_help(bot, update, lS)
		elif message in LanguageSupport.allVariants(ABOUT_BUTTON):
			self.command_about(bot, update, lS)
		elif message in LanguageSupport.allVariants(OTHER_BOTS_BUTTON):
			self.command_otherbots(bot, update, lS)

		# elif message == EN_LANG_BUTTON:
		# 	self.command_set_lang_en(bot, update, lS)
		# elif message == RU_LANG_BUTTON:
		# 	self.command_set_lang_ru(bot, update, lS)

		elif message in LanguageSupport.allVariants(GIMMEPIC_BUTTON):
			self.command_gimmepic(bot, update, lS)
		elif message in LanguageSupport.allVariants(SUBSCRIBE_BUTTON):
			self.command_subscribe(bot, update, lS)
		elif message in LanguageSupport.allVariants(UNSUBSCRIBE_BUTTON):
			self.command_unsubscribe(bot, update, lS)
		elif message in LanguageSupport.allVariants(SHOW_PERIOD_BUTTON):
			self.command_show_period(bot, update, lS)

		else:
			if not self.setPeriod(bot, update, lS):
				self.unknown_command(bot, update, lS)

	# noinspection PyArgumentList
	@_command_method
	def unknown_command(self, bot, update, lS=None):
		self.sendMessageCommandMethod(bot, update, UNKNOWN_COMMAND_MESSAGE)

	def error_handler(self, bot, update, error):
		print(error)

	# PICBOT COMMANDS

	# noinspection PyArgumentList
	@_command_method
	def command_gimmepic(self, bot, update, lS=None):
		chat_id = update.message.chat_id
		self.doGimmepic(chat_id)

	# noinspection PyArgumentList
	@_command_method
	def command_subscribe(self, bot, update, lS=None):
		chat_id = update.message.chat_id
		period = self.database_handler.getPeriod(chat_id)
		if self.database_handler.getSubscribed(chat_id):
			self.sendMessageCommandMethod(bot, update, lS(ALREADY_SUBSCRIBED_MESSAGE).format(period))
		else:
			self.database_handler.subscribeUser(chat_id)
			self.database_handler.resetTimer(chat_id)
			self.createPeriodicSenderTask(chat_id)
			self.sendMessageCommandMethod(bot, update, lS(SUBSCRIBED_MESSAGE).format(period))

	# noinspection PyArgumentList
	@_command_method
	def command_unsubscribe(self, bot, update, lS=None):
		chat_id = update.message.chat_id
		if not self.database_handler.getSubscribed(chat_id):
			self.sendMessageCommandMethod(bot, update, lS(NOT_SUBSCRIBED_YET_MESSAGE))
		else:
			self.database_handler.unsubscribeUser(chat_id)
			self.removePeriodicSenderTask(chat_id)
			self.sendMessageCommandMethod(bot, update, lS(UNSUBSCRIBED_MESSAGE))

	# noinspection PyArgumentList
	@_command_method
	def command_show_period(self, bot, update, lS=None):
		chat_id = update.message.chat_id
		period = self.database_handler.getPeriod(chat_id)
		self.sendMessageCommandMethod(bot, update, """An image is sent to you every {0} seconds.""".format(period))


	# noinspection PyArgumentList
	@_command_method
	def command_spamuncached(self, bot, update, lS=None):
		chat_id = update.message.chat_id
		self.sendUncachedImages(chat_id, self.pic_source)