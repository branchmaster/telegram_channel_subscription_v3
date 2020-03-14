#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import time
from telegram.ext import Updater, MessageHandler, Filters
from telegram import InputMediaPhoto
from db import SUBSCRIPTION
from db import QUEUE
import threading
import traceback as tb
from telegram_util import log_on_fail
from command import handleCommand

dbs = SUBSCRIPTION()
queue = QUEUE()
media = {}

with open('CREDENTIALS') as f:
    CREDENTIALS = yaml.load(f, Loader=yaml.FullLoader)

tele = Updater(CREDENTIALS['bot_token'], use_context=True)
bot = tele.bot
debug_group = bot.get_chat(-1001198682178)

INTERVAL = 60 * 60

@log_on_fail(debug_group)
def command(update, context):
    handleCommand(update, context, dbs)

def addHold(update, context):
    return

@log_on_fail(debug_group)
def addQueueImp(msg):
    if not dbs.getSubsribers(msg.chat_id):
        return
    try:
        msg.forward(debug_group.id)
    except:
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

def addQueue(msg):
    addQueueImp(msg)

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
    forwarded = set()
    while not queue.empty():
        item = queue.pop()
        reciever, chat_id, message_id = item
        if (chat_id, message_id) in forwarded:
            queue_to_push_back.append(item)
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
            if str(e) not in ['Message to forward not found', 'Message_id_invalid']:
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