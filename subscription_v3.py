#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import time
from telegram.ext import Updater, MessageHandler, Filters
from telegram import InputMediaPhoto
from db import SUBSCRIPTION, QUEUE, HOLD, CACHE
import threading
import traceback as tb
from telegram_util import log_on_fail
from command import handleCommand

dbs = SUBSCRIPTION()
queue = QUEUE()
dbh = HOLD()
cache = CACHE()

with open('CREDENTIALS') as f:
    CREDENTIALS = yaml.load(f, Loader=yaml.FullLoader)

tele = Updater(CREDENTIALS['bot_token'], use_context=True)
bot = tele.bot
debug_group = bot.get_chat(-1001198682178)

INTERVAL = 60 * 60

@log_on_fail(debug_group)
def command(update, context):
    handleCommand(update, context, dbs)

@log_on_fail(debug_group)
def addHold(update, context):
    msg = update.message
    if msg:
        dbh.hold(msg.chat_id, msg)

@log_on_fail(debug_group)
def addQueue(msg):
    if not dbs.getSubsribers(msg.chat_id):
        return
    for reciever in dbs.getSubsribers(msg.chat_id):
        # I'm worried about order...
        queue.append((reciever, msg.chat_id, msg.message_id, msg.media_group_id)) 

@log_on_fail(debug_group)
def manage(update, context):
    threading.Timer(INTERVAL, addQueue, [update.channel_post]).start() 

tele.dispatcher.add_handler(MessageHandler(
    (~Filters.private) & Filters.command, command))
tele.dispatcher.add_handler(MessageHandler(
    Filters.update.channel_posts & (~Filters.command), manage))
tele.dispatcher.add_handler(MessageHandler(
    Filters.update.channel_posts | Filters.group, addHold), group=2)

def forwardMsg(item):
    reciever, chat_id, message_id, media_group_id = item
    if not media_group_id:
        bot.forward_message(
            chat_id = reciever,
            from_chat_id = chat_id,
            message_id = message_id)
        return
    for message_id in queue.pop_all(reciever, chat_id, media_group_id):
        try:
            r = bot.forward_message(
                chat_id = debug_group.id, 
                from_chat_id = chat_id,
                message_id = message_id)
            r.delete()
            media = []
            if r.photo[-1].file_id not in [x.media for x in media]:
                media.append(InputMediaPhoto(r.photo[-1].file_id, 
                    caption=r.caption_markdown, parse_mode='Markdown'))
            bot.send_media_group(reciever, media)
        except:
            return

@log_on_fail(debug_group)
def loopImp():
    queue_to_push_back = []
    while not queue.empty():
        item = queue.pop()
        queue_to_push_back.append(item)
        reciever, chat_id, message_id, media_group_id = item
        if dbh.onHold(reciever):
            continue
        try:
            r = bot.forward_message(
                chat_id = debug_group.id, 
                from_chat_id = chat_id,
                message_id = message_id)
            r.delete()
            if dbh.onHold((r.forward_from.chat_id, r.forward_from.message_id)):
                continue
            if not cache.add((reciever, r.forward_from.chat_id, r.forward_from.message_id)):
                queue_to_push_back.pop()
                continue
        dbh.hold((r.forward_from.chat_id, r.forward_from.message_id))
        dbh.hold(reciever)
        forwardMsg(item)
        except Exception e:
            print(e) # debug
            continue
        try:
            forwardMsg(item)
        except Exception as e:
            tb.print_exc()
            print(item)
            debug_group.send_message(str(e))
            queue_to_push_back.append(item)
    queue.replace(queue_to_push_back)

def loop():
    loopImp()
    threading.Timer(INTERVAL, loop).start() 

threading.Timer(1, loop).start()

tele.start_polling()
tele.idle()