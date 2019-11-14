#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import yaml
import time
from telegram.ext import Updater, MessageHandler, Filters
from db import SUBSCRIPTION
from db import UPDATE_TIME
import threading
import traceback as tb
import hashlib
from telegram_util import isMeaningful, splitCommand, log_on_fail, autoDestroy

START_MESSAGE = ('''
Channel Subscription for channels and groups. Bot needs to be in the subscribed channel.
''')

dbs = SUBSCRIPTION()
dbu = UPDATE_TIME()
queue = []
cache = {}
hashes = {}

SEC_PER_MIN = 60

with open('CREDENTIALS') as f:
    CREDENTIALS = yaml.load(f, Loader=yaml.FullLoader)

with open('config') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

test_channel = -1001459876114
debug_group = CREDENTIALS.get('debug_group') or -1001198682178
m_interval = config['message_interval_min']
updater = Updater(CREDENTIALS['bot_token'], use_context=True)

def tryDeleteById(chat_id, msg_id):
    try:
        updater.bot.delete_message(chat_id = chat_id, message_id = msg_id)
    except:
        pass

def getChat(raw, msg):
    raw = str(raw).strip().split('/')[-1]
    try:
        float(raw)
    except:
        if raw and raw[0] != '@':
            raw = '@' + raw
    try:
        result = updater.bot.sendMessage(raw, 'test') 
        result.delete()
        return result.chat
    except Exception as e:
        r = msg.reply_text('roomId invalid: ' + raw, quote=False)
        autoDestroy(r)
        return None

def formatSubscription(s):
    return '[' + s['title'] + '](t.me/' + str(s.get('username')) + ')'

@log_on_fail(updater)
def command(update, context):
    msg = update.effective_message
    autoDestroy(msg)
    command, text = splitCommand(msg.text)
    if 's3_l' in command:
        subscriptions = dbs.getList(msg.chat_id)
        subscriptions = [str(index) + ': ' + formatSubscription(x) for \
            index, x in enumerate(subscriptions)]
        r = msg.reply_text(
            'subscription list: \n\n' + '\n'.join(subscriptions), 
            quote=False,
            parse_mode='Markdown', 
            disable_web_page_preview=True)
        autoDestroy(r)
        return
    if 's3_un' in command:
        try:
            index = int(text)
        except:
            r = msg.reply_text('please give index')
            autoDestroy(r)
            return
        r = dbs.deleteIndex(msg.chat_id, index)
        autoDestroy(msg.reply_text(r, quote = False))
        return
    if 's3_s' in command:
        chat = getChat(text, msg)
        if not chat:
            return
        r = dbs.add(msg.chat_id, chat.to_dict())
        autoDestroy(msg.reply_text(r, quote=False))
        return

@log_on_fail(updater)
def manage(update, context):
    global queue
    msg = update.effective_message
    if (not msg) or (not isMeaningful(msg)):
        return 
    chat_id = msg.chat_id
    if chat_id and chat_id < 0 and dbs.getList(chat_id):
        dbu.setTime(chat_id)
    for subscriber in dbs.getSubsribers(chat_id)[::-1]:
        queue.append((subscriber, msg.chat_id, msg.message_id)) 

def start(update, context):
    if update.message:
        update.message.reply_text(START_MESSAGE)

updater.dispatcher.add_handler(MessageHandler((~Filters.private) and (Filters.command), command))
updater.dispatcher.add_handler(MessageHandler((~Filters.private) and (~Filters.command), manage))
updater.dispatcher.add_handler(MessageHandler(Filters.private, start))

def isReady(subscriber):
    return dbu.get(subscriber) + m_interval * SEC_PER_MIN < time.time()

def findDup(msg):
    global hashes
    s = str(msg.chat_id) + str(msg.text) + str(msg.photo)
    s = s.encode('utf-8')
    h = hashlib.sha224(s).hexdigest()
    if h in hashes:
        return hashes[h]
    hashes[h] = msg.message_id

@log_on_fail(updater)
def loopImp():
    global queue
    queue_to_push_back = []
    while queue:
        item = queue.pop()
        subscriber, chat_id, message_id = item
        if not isReady(subscriber):
            queue_to_push_back.append(item)
            continue
        try:
            if item in cache:
                tryDeleteById(subscriber, cache[item])
            r = updater.bot.forward_message(
                chat_id = subscriber,
                from_chat_id = chat_id,
                message_id = message_id)
            cache[item] = r.message_id
            dup_msg = findDup(r)
            if dup_msg:
                tryDeleteById(subscriber, dup_msg)
            dbu.setTime(subscriber)
        except Exception as e:
            if str(e) not in ['Message to forward not found', 'Message_id_invalid']:
                print(e)
                tb.print_exc()
                print(item)
                updater.bot.send_message(chat_id=debug_group, text=str(e))
                queue_to_push_back.append(item)
    for item in queue_to_push_back[::-1]:
        queue.append(item)

def loop():
    loopImp()
    threading.Timer(m_interval * SEC_PER_MIN, loop).start() 

threading.Timer(1, loop).start()

updater.start_polling()
updater.idle()