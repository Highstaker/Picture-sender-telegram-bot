from os import path
from time import sleep
import io

from telegram import ReplyKeyboardMarkup, ParseMode, ReplyKeyboardHide, error, Bot

from logging_handler import LoggingHandler
log = LoggingHandler(__name__)


class BadFileIDError(Exception):
	def __init__(self, message=""):
		super(BadFileIDError, self).__init__()

		self.message = message

		log.error("BadFileIDError: " + message)

	def __str__(self):
		return self.message


# noinspection PyShadowingNames
class BotRoutines(Bot):
	"""
	Generic bot functions made a bit more clear.
	"""

	def __init__(self, token, default_markdown="markdown"):
		super(BotRoutines, self).__init__(token=token)
		self.default_markdown = self.setMarkdown(default_markdown)

	@staticmethod
	def setMarkdown(markdown):
		"""
		Returns the markdown as it is understood by the bot.
		:param markdown: a string representing a markdown. Can be `html` or `markdown`
		:return: ParseMode.something or None
		"""
		if markdown == "markdown":
			return ParseMode.MARKDOWN
		elif markdown == "html":
			return ParseMode.HTML
		else:
			return None

	@staticmethod
	def breakLongMessage(msg, max_chars_per_message=2048):
		"""
		Breaks a message that is too long.
		:param max_chars_per_message: maximum amount of characters per message.
		The official maximum is 4096.
		Changing this is not recommended.
		:param msg: message to be split
		:return: a list of message pieces
		"""

		# let's split the message by newlines first
		message_split = msg.split("\n")

		# the result will be stored here
		broken = []

		# splitting routine
		while message_split:
			result = message_split.pop(0) + "\n"
			if len(result) > max_chars_per_message:
				# The chunk is huge. Split it not caring for newlines.
				broken += [result[i:i + max_chars_per_message].strip("\n\t\r ")
						   for i in range(0, len(result), max_chars_per_message)]
			else:
				# It's a smaller chunk, append others until their sum is bigger than maximum
				while len(result) <= max_chars_per_message:
					if not message_split:
						# if the original ran out
						break
					# check if the next chunk makes the merged chunk it too big
					if len(result) + len(message_split[0]) <= max_chars_per_message:
						# nope. append chunk
						result += message_split.pop(0) + "\n"
					else:
						# yes, it does. Stop on this.
						break
				broken += [result.strip("\n\t\r ")]

		return broken

	@staticmethod
	def getPhotoFileID(msg):
		return msg['photo'][-1]['file_id']

	def sendPhoto(self, chat_id, photo, caption=None, **kwargs):
		if isinstance(photo, bytes):
			# It is a bytestring
			pic = io.BufferedReader(io.BytesIO(photo))
			sent_msg = super(BotRoutines, self).sendPhoto(chat_id, pic, caption)
		else:
			try:
				with open(photo, "rb") as pic:
					sent_msg = super(BotRoutines, self).sendPhoto(chat_id, pic, caption)
			except FileNotFoundError:
				# it's an ID
				try:
					sent_msg = super(BotRoutines, self).sendPhoto(chat_id, photo, caption)
				except error.BadRequest:
					# bad ID. Do nothing
					sent_msg = None
					raise BadFileIDError("File ID is probably broken")
		return sent_msg

	def sendMessageCommandMethod(self, bot, update, text, *args, **kwargs):
		chat_id = update.message.chat_id
		self.sendMessage(chat_id, text, *args, **kwargs)

	def sendMessage(self, chat_id, text, markdown=None, key_markup=None, disable_web_page_preview=True):
		"""

		:param chat_id:
		:param text:
		:param markdown: "markdown" or "html". If set to any other string - no markdown.
		If None - default markdown is used.
		:param key_markup: a list of lists of buttons. If "hide" - hide keyboard.
		:type key_markup: list, str, None
		:param disable_web_page_preview:
		:return:
		"""
		# chat_id = update.message.chat_id
		msg = text

		if not markdown:
			parse_mode = self.default_markdown
		else:
			parse_mode = self.setMarkdown(markdown)

		if key_markup == "hide":
			reply_markup = ReplyKeyboardHide()
		elif key_markup is None:
			reply_markup = None
		else:
			reply_markup = ReplyKeyboardMarkup(key_markup, resize_keyboard=True)

		def send(l_parse_mode):
			super(BotRoutines, self).sendMessage(chat_id=chat_id, text=m,
												 reply_markup=reply_markup,
												 parse_mode=l_parse_mode,
												 disable_web_page_preview=disable_web_page_preview,
												 )

		for m in self.breakLongMessage(msg):
			try:
				send(parse_mode)
			except error.BadRequest:
				# message could have a broken markdown
				send(None)


if __name__ == '__main__':
	# TESTS
	with open(path.join("tokens", "testbot")) as f:
		parse = f.read().split("\n")
	TOKEN = parse[0].split("#")[0].strip(" \n\r\t")  # your bot token
	chat_id = int(parse[1].split("#")[0])  # your chat_id in your test bot

	routines = BotRoutines(TOKEN)

	##############
	# ACTUAL TESTS
	##############

	##################
	# breakLongMessage

	#############
	# sendMessage

	# simple message
	routines.sendMessage(chat_id=chat_id, text="hello")

	# markdowns
	routines.sendMessage(chat_id=chat_id, text="*with* _mark_`downs`")
	routines.sendMessage(chat_id=chat_id, text="*bold*")
	routines.sendMessage(chat_id=chat_id, text="_italic_")
	routines.sendMessage(chat_id=chat_id, text="`code`")
	routines.sendMessage(chat_id=chat_id, text="[link](example.com)")

	# same without markdowns
	routines.sendMessage(chat_id=chat_id, text="no markdowns", markdown="no")
	routines.sendMessage(chat_id=chat_id, text="*bold*", markdown="no")
	routines.sendMessage(chat_id=chat_id, text="_italic_", markdown="no")
	routines.sendMessage(chat_id=chat_id, text="`code`", markdown="no")
	routines.sendMessage(chat_id=chat_id, text="[link](example.com)", markdown="no")

	# html tags
	routines.sendMessage(chat_id=chat_id, text="HTML")
	routines.sendMessage(chat_id=chat_id, text="<b>bold</b>", markdown="html")
	routines.sendMessage(chat_id=chat_id, text="<i>italic</i>", markdown="no")
	routines.sendMessage(chat_id=chat_id, text='<a href="http://google.com">link</a>', markdown="no")

	# broken markdowns
	routines.sendMessage(chat_id=chat_id, text="*with broken _markdowns`")
	routines.sendMessage(chat_id=chat_id, text="<b>with <i>broken HTML markdowns", markdown="html")

	# long message
	routines.sendMessage(chat_id=chat_id, text="0" * 3000)

	# webpage preview
	routines.sendMessage(chat_id=chat_id, text="www.google.com", disable_web_page_preview=True)
	routines.sendMessage(chat_id=chat_id, text="www.google.com", disable_web_page_preview=False)

	# keyboard markup
	routines.sendMessage(chat_id=chat_id, text="keyboard", key_markup=[["a", "b", "c"], ["d", "e"], ["f"]])
	sleep(1)
	routines.sendMessage(chat_id=chat_id, text="keyboard", key_markup=None)
	sleep(1)
	routines.sendMessage(chat_id=chat_id, text="hide keyboard", key_markup="hide")

	###########
	# sendPhoto

	test_id = routines.getPhotoFileID(routines.sendPhoto(chat_id, path.join("tests", "test_pics", "pic1.png")))
	routines.sendPhoto(chat_id, path.join("tests", "test_pics", "pic2.jpeg"))
	routines.sendPhoto(chat_id, path.join("tests", "test_pics", "pic3.jpg"))

	routines.sendPhoto(chat_id, path.join("tests", "test_pics", "pic3.jpg"), caption="Test pic")

	# sending by ID
	routines.sendPhoto(chat_id, test_id)

	# broken ID
	try:
		routines.sendPhoto(chat_id, "AgADAgADDq8xG-wJfgrdQ52w0GAAAAclcQ0ABKabtVnUAX_Q-YcBAAEC")
	except BadFileIDError as e:
		print(e)
		print("passed!")


########
# finish
########
# updater.stop()
