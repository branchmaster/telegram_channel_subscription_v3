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
        queue.append((reciever, msg.chat_id, msg.message_id, msg.media_group_id)) 
        # get all the related message when forwarding...
        # move all logic when forwarding
        # if msg.media_group_id:
        #     if (reciever, msg.chat_id, msg.media_group_id) not in queue.queue:
        #         queue.append((reciever, msg.chat_id, msg.media_group_id))
        #     media[msg.media_group_id] = media.get(msg.media_group_id, [])
        #     if msg.photo[-1].file_id not in [x.media for x in media[msg.media_group_id]]:
        #         imp = InputMediaPhoto(msg.photo[-1].file_id, caption=msg.caption_markdown, parse_mode='Markdown')
        #         media[msg.media_group_id].append(imp)

@log_on_fail(debug_group)
def manage(update, context):
    threading.Timer(INTERVAL, addQueue, [update.channel_post]).start() 

tele.dispatcher.add_handler(MessageHandler(
    (~Filters.private) & Filters.command, command))
tele.dispatcher.add_handler(MessageHandler(
    Filters.update.channel_posts & (~Filters.command), manage))
tele.dispatcher.add_handler(MessageHandler(
    Filters.update.channel_posts | Filters.group, addHold), group=2)

@log_on_fail(debug_group)
def loopImp():
    queue_to_push_back = []
    while not queue.empty():
        item = queue.pop()
        reciever, chat_id, message_id, media_group_id = item
        if dbh.onHold(reciever) or dbh.onHold((chat_id, message_id)):
            queue_to_push_back.append(item)
            continue
        try:
            r = bot.forward_message(
                chat_id = debug_group.id, 
                from_chat_id = chat_id,
                message_id = message_id)
            r.delete()
            if not cache.add((reciever, r.forward_from.chat_id, r.forward_from.message_id)):
                continue
        except Exception e:
            print(e) # debug
            continue
        forwarded.add((chat_id, message_id))
        try:
            if message_id in media:
                debug_group.send_message(len(media[message_id]))
                r = bot.send_media_group(reciever, media[message_id])[0]
            else:
                r = bot.forward_message(
                    chat_id = reciever,
                    from_chat_id = chat_id,
                    message_id = message_id)
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