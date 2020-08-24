from telegram.ext import Updater

with open('CREDENTIALS') as f:
    token = f.read().strip()

tele = Updater(token, use_context=True)
bot = tele.bot
debug_group = bot.get_chat(420074357)