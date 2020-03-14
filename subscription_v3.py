#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
from telegram.ext import Updater, MessageHandler, Filters
from telegram import InputMediaPhoto
from db import SUBSCRIPTION, QUEUE, HOLD, CACHE, HOUR
import threading
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
    orig_msg = (msg.forward_from_chat.id, msg.forward_from_message_id) if msg.forward_from_chat else (msg.chat_id, msg.message_id)
    dbh.hold(orig_msg, hold_hour = 5)
    cache.add((msg.chat_id, orig_msg[0], orig_msg[1]))

    hold_hour = 1 if msg.chat_id == 1001197970228 else 3 # Hack...
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
        return [bot.forward_message(chat_id = reciever,
            from_chat_id = chat_id, message_id = message_id)]
    media = []
    for mid in queue.pop_all(reciever, chat_id, media_group_id) + [message_id]:
        try:
            r = bot.forward_message(chat_id = debug_group.id, 
                from_chat_id = chat_id, message_id = mid)
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
            r = bot.forward_message(chat_id = debug_group.id, 
                from_chat_id = chat_id, message_id = message_id)
            r.delete()
        except:
            queue_to_push_back.pop()
            continue

        orig_msg = (r.forward_from_chat.id, r.forward_from_message_id) \
            if r.forward_from_chat else (chat_id, message_id)

        if dbh.onHold(orig_msg):
            continue

        if not cache.add((reciever, orig_msg[0], orig_msg[1])):
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