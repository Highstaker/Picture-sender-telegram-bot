# from telegramHigh import TelegramHigh
import telegram

with open("testbot_token", "r") as f:
	BOT_TOKEN = f.read().strip("\n")

print("BOT_TOKEN = ", BOT_TOKEN, "!!!", sep="")

bot = telegram.Bot(BOT_TOKEN)
u = bot.getUpdates()[-1]
chat_id =  u.message.chat_id
print("chat_id = ", chat_id)
