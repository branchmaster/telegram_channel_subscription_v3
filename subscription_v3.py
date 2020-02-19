#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import time
from telegram.ext import Updater, MessageHandler, Filters
from db import SUBSCRIPTION
from db import UPDATE_TIME
from db import QUEUE
import threading
import traceback as tb
import hashlib
from telegram_util import isMeaningful, splitCommand, log_on_fail, autoDestroy

START_MESSAGE = ('''
Channel Subscription for channels and groups. Bot needs to be in the subscribed channel.
''')

dbs = SUBSCRIPTION()
dbu = UPDATE_TIME()
queue = QUEUE()
media = {}
cache = {}
hashes = {}

with open('CREDENTIALS') as f:
    CREDENTIALS = yaml.load(f, Loader=yaml.FullLoader)

with open('config') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

test_channel = -1001459876114
m_interval = config['message_interval_min']
tele = Updater(CREDENTIALS['bot_token'], use_context=True)
debug_group = tele.bot.get_chat(-1001198682178)

INTERVAL = m_interval * 60

def tryDeleteById(chat_id, msg_id):
    try:
        tele.bot.delete_message(chat_id = chat_id, message_id = msg_id)
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
        result = tele.bot.sendMessage(raw, 'test') 
        result.delete()
        return result.chat
    except Exception as e:
        r = msg.reply_text('roomId invalid: ' + raw, quote=False)
        autoDestroy(r)
        return None

def formatSubscription(s):
    return '[' + s['title'] + '](t.me/' + str(s.get('username')) + ')'

@log_on_fail(debug_group)
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
    if 'pause' in command:
        chat_id = msg.chat_id
        if chat_id and chat_id < 0 and dbs.getList(chat_id):
            dbu.setPause(chat_id)
        autoDestroy(msg.reply_text('success', quote=False))
        return

def isMeaningfulNew(msg):
    if isMeaningful(msg):
        return True
    return not not msg.media_group_id

@log_on_fail(debug_group)
def manage(update, context):
    global queue
    msg = update.channel_post
    if (not msg) or (not isMeaningfulNew(msg)):
        return 
    chat_id = msg.chat_id
    if chat_id and chat_id < 0 and dbs.getList(chat_id):
        dbu.setTime(chat_id)
    for subscriber in dbs.getSubsribers(chat_id)[::-1]:
        if msg.media_group_id:
            queue.append((subscriber, msg.chat_id, msg.media_group_id))
            media[msg.media_group_id] = media.get(msg.media_group_id, [])
            media[msg.media_group_id].append(msg.photo)
        else:
            queue.append((subscriber, msg.chat_id, msg.message_id)) 

def start(update, context):
    if update.message:
        update.message.reply_text(START_MESSAGE)

tele.dispatcher.add_handler(MessageHandler((~Filters.private) and (Filters.command), command))
tele.dispatcher.add_handler(MessageHandler(Filters.update.channel_posts and (~Filters.command), manage))
tele.dispatcher.add_handler(MessageHandler(Filters.private, start))

def isReady(subscriber):
    return dbu.get(subscriber) + INTERVAL < time.time()

def findDup(msg):
    global hashes
    s = str(msg.chat_id) + str(msg.text) + str(msg.photo)
    s = s.encode('utf-8')
    h = hashlib.sha224(s).hexdigest()
    if h in hashes:
        return hashes[h]
    hashes[h] = msg.message_id

@log_on_fail(debug_group)
def loopImp():
    global queue
    queue_to_push_back = []
    forwarded = set()
    while not queue.empty():
        item = queue.pop()
        subscriber, chat_id, message_id = item
        if (not isReady(subscriber)) or \
            (chat_id, message_id) in forwarded:
            queue_to_push_back.append(item)
            continue
        forwarded.add((chat_id, message_id))
        try:
            if item in cache:
                tryDeleteById(subscriber, cache[item])
            if message_id in media:
                r = tele.bot.send_media_group(subscriber, media[message_id])[0]
            else:
                r = tele.bot.forward_message(
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
                debug_group.send_message(str(e))
                queue_to_push_back.append(item)
    for item in queue_to_push_back[::-1]:
        queue.append(item)

def loop():
    loopImp()
    threading.Timer(INTERVAL, loop).start() 

threading.Timer(1, loop).start()

tele.start_polling()
tele.idle()