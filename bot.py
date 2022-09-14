from telegram import Bot
import config
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, run_async, JobQueue
from telegram.error import BadRequest
from bs4 import BeautifulSoup
import requests
import os
import json

token = config.TOKEN

if os.path.exists('lastgame.txt'):
    with open('lastgame.txt', 'r') as lg:
        temp_lg = lg.read()
        last_game = temp_lg.split("&&&")
else:
    last_game = ["", ""]

if os.path.exists('data.json'):
    with open('data.json', 'r') as chat_data:
        chat_db = json.load(chat_data)
else:
    chat_db = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update, context):
    bot = context.bot
    user = update.effective_user
    bot.sendMessage(update.effective_chat.id, config.START_MESSAGE)

def help_command(update, context):
    bot = context.bot
    user = update.effective_user
    bot.sendMessage(update.effective_chat.id, config.HELP_MESSAGE)

def get_new_game(context):
    global last_game
    try:
        url = requests.get("https://www.indiegamebundles.com/category/free/feed/")
        soup = BeautifulSoup(url.content, 'xml')
        entry = soup.find('item')
        title = entry.title.text
        link = entry.link.text
    except Exception as e:
        print(e)
        return 
    try:
        bot = context.bot
    except Exception as e:
        print(e)
        return 
    if last_game[0] != title:
        last_game[0] = title
        last_game[1] = link
        with open('lastgame.txt', 'w') as lg:
            lg.write(title + "&&&" + link)
        for id in chat_db.values():
            try:
                bot.send_message(id, f"{title}\n{link}")
            except Exception as e:
                print(e)
                return 
    return f"{title}\n{link}"




def get_current_game(update, context):
    bot = context.bot
    chat_id = update.effective_chat.id
    if last_game[0] == "":
        get_new_game('')
    bot.send_message(chat_id, last_game[0] + "\n" + last_game[1])

def subscribe(update, context):
    bot = context.bot
    chat_id = update.effective_chat.id
    if update.effective_chat.type == 'group':
        chat_name = update.effective_chat.title + str(update.effective_chat.id)
    else:
        chat_name = update.effective_chat.username
    for id in chat_db.values():
        if chat_id == id:
            bot.send_message(chat_id, "You are already subscirbed!")
            return
    chat_db.update({chat_name: chat_id})
    with open('data.json', 'w') as chat_data:
        json.dump(chat_db, chat_data)
    bot.send_message(chat_id, "You have been subscribed!")

def unsubscribe(update, context):
    bot = context.bot
    chat_id = update.effective_chat.id
    for key, id in chat_db.items():
        if chat_id == id:
            del chat_db[key]
            with open('data.json', 'w') as chat_data:
                json.dump(chat_db, chat_data)
                bot.send_message(chat_id, "You have succefully unsubscribed!")
                return
    bot.send_message(update.effective_chat.id, "You are not even subscribed!")
    return




def main():
    updater = Updater(token=token, use_context=True)
    dp = updater.dispatcher
    job_queue = JobQueue()
    job_queue.set_dispatcher(dp)
    job_queue.run_repeating(callback=get_new_game, interval=3600)
    logger.info("Bot started.")
    dp.add_handler(CommandHandler("getgame", get_current_game))
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("subscribe", subscribe))
    dp.add_handler(CommandHandler("unsubscribe", unsubscribe))
    job_queue.start()
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
