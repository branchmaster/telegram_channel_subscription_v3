#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import time
from telegram.ext import Updater, MessageHandler, Filters
from telegram import InputMediaPhoto
from db import SUBSCRIPTION, QUEUE, HOLD, CACHE, HOUR
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

@log_on_fail(debug_group)
def command(update, context):
    handleCommand(update, context, dbs)

def hold(msg):
    orig_msg = msg.forward_from if msg.forward_from else msg
    dbh.hold((orig_msg.chat_id, orig_msg.message_id), hold_hour = 5)
    cache.add((msg.chat_id, orig_msg.chat_id, orig_msg.forward_from.message_id))

    if msg.chat_id == 1001197970228: # Hack...
        hold_hour = 1
    else:
        hold_hour = 3
    dbh.hold(msg.chat_id, hold_hour=hold_hour)

@log_on_fail(debug_group)
def addHold(update, context):
    if update.message:
        hold(update.message)

@log_on_fail(debug_group)
def manage(update, context):
    msg = update.channel_post
    for reciever in dbs.getSubsribers(msg.chat_id):
        queue.append((reciever, msg.chat_id, msg.message_id, msg.media_group_id))
        hold(msg)

tele.dispatcher.add_handler(MessageHandler(
    (~Filters.private) & Filters.command, command))
tele.dispatcher.add_handler(MessageHandler(
    Filters.update.channel_posts & (~Filters.command), manage))
tele.dispatcher.add_handler(MessageHandler(
    Filters.update.channel_posts | Filters.group, addHold), group=2)

def forwardMsg(item):
    reciever, chat_id, message_id, media_group_id = item
    if not media_group_id:
        return [bot.forward_message(
            chat_id = reciever,
            from_chat_id = chat_id,
            message_id = message_id)]
    media = []
    for message_id in queue.pop_all(reciever, chat_id, media_group_id):
        try:
            r = bot.forward_message(
                chat_id = debug_group.id, 
                from_chat_id = chat_id,
                message_id = message_id)
            r.delete()
        except:
            pass
        if r.photo[-1].file_id not in [x.media for x in media]:
            media.append(InputMediaPhoto(r.photo[-1].file_id, 
                caption=r.caption_markdown, parse_mode='Markdown'))
    if media:
        return bot.send_media_group(reciever, media)
    return []

@log_on_fail(debug_group)
def loopImp():
    dbh.clearHold(debug_group)
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
        except:
            queue_to_push_back.pop()
            continue

        if dbh.onHold((r.forward_from.chat_id, r.forward_from.message_id)):
            continue

        if not cache.add((reciever, r.forward_from.chat_id, r.forward_from.message_id)):
            queue_to_push_back.pop()
            continue

        for m in forwardMsg(item):
            hold(m)
        hold(r)
    queue.replace(queue_to_push_back)

def loop():
    loopImp()
    threading.Timer(HOUR, loop).start() 

threading.Timer(1, loop).start()

tele.start_polling()
tele.idle()