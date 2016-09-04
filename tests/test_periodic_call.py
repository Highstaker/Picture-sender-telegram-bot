from os import path

from telegram.ext import Updater, CommandHandler, Job

timers = dict()


def start(bot, update):
	bot.sendMessage(update.message.chat_id, text='Hi! Use /set <seconds> to ' 'set a timer')


def alarm(bot, job):
	"""Function to send the alarm message"""
	bot.sendMessage(job.context, text='Beep!')


def set_timer(bot, update, args, job_queue):
	"""Adds a job to the queue"""
	chat_id = update.message.chat_id
	try:
		# args[0] should contain the time for the timer in seconds
		due = int(args[0])
		if due < 0:
			bot.sendMessage(chat_id, text='Sorry we can not go back to future!')
			return

		# Add job to queue
		job = Job(alarm, due, repeat=True, context=chat_id)
		timers[chat_id] = job
		# job_queue.put(job)

		bot.sendMessage(chat_id, text='Timer successfully set!')

	except (IndexError, ValueError):
		bot.sendMessage(chat_id, text='Usage: /set <seconds>')

def main(TOKEN):
	updater = Updater(TOKEN)

	# Get the dispatcher to register handlers
	dp = updater.dispatcher

	# on different commands - answer in Telegram
	dp.add_handler(CommandHandler("start", start))
	dp.add_handler(CommandHandler("help", start))
	dp.add_handler(CommandHandler("set", set_timer, pass_args=True, pass_job_queue=True))
	# dp.add_handler(CommandHandler("unset", unset, pass_job_queue=True))

	# log all errors
	# dp.add_error_handler(error)
	#
	# Start the Bot
	updater.start_polling()

	# Block until the you presses Ctrl-C or the process receives SIGINT,
	# SIGTERM or SIGABRT. This should be used most of the time, since
	# start_polling() is non-blocking and will stop the bot gracefully.
	# try:
	updater.idle()
	# except KeyboardInterrupt:
	# 	updater.stop()


if __name__ == '__main__':
	with open(path.join(path.dirname(path.dirname(path.realpath(__file__))), "tokens", "testbot"), 'r') as f:
		parse = f.read().split("\n")
		TOKEN = parse[0].split("#")[0].strip()
		print(TOKEN)
		# chat_id = parse[1]

	main(TOKEN)
