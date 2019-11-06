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

START_MESSAGE = ('''
Channel Subscription for channels and groups. Bot needs to be in the subscribed channel.
''')

dbs = SUBSCRIPTION()
dbu = UPDATE_TIME()
queue = []
cache = {}

with open('CREDENTIALS') as f:
    CREDENTIALS = yaml.load(f, Loader=yaml.FullLoader)

with open('config') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

test_channel = -1001459876114
debug_group = CREDENTIALS.get('debug_group') or -1001198682178
m_interval = config['message_interval_min']

def isMeaningful(m):
    if m.photo:
        return True
    if not m.text:
        return False
    if m.text.startswith('/'):
        return False
    if len(m.text) < 10:
        return False
    return True

def tryDelete(msg):
    try:
        msg.delete()
    except:
        pass

def autoDestroy(msg):
    threading.Timer(60, lambda: tryDelete(msg)).start() 

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

def splitCommand(text):
    pieces = text.split()
    if len(pieces) < 1:
        return '', ''
    command = pieces[0]
    return command.lower(), text[text.find(command) + len(command):].strip()

def formatSubscription(s):
    return '[' + s['title'] + '](t.me/' + str(s['username']) + ')'

def command(update, context):
    try:
        msg = update.message
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
    except Exception as e:
        updater.bot.send_message(chat_id=debug_group, text=str(e)) 
        print(e)
        tb.print_exc()

def manage(update, context):
    global queue
    try:
        msg = update.message
        if (not msg) or (not isMeaningful(msg)):
            return 
        chat_id = msg.chat_id
        if chat_id and chat_id > 0 and dbs.getList(chat_id):
            dbu.setTime(chat_id)
        for subscriber in dbs.getSubsribers(chat_id):
            queue.append((subscriber, msg.chat_id, msg.message_id))
    except Exception as e:
        updater.bot.send_message(chat_id=debug_group, text=str(e)) 
        print(e)
        tb.print_exc()   

def start(update, context):
    if update.message:
        update.message.reply_text(START_MESSAGE, quote=False)

updater = Updater(CREDENTIALS['bot_token'], use_context=True)
dp = updater.dispatcher

dp.add_handler(MessageHandler((~Filters.private) and (Filters.command), command))
dp.add_handler(MessageHandler((~Filters.private) and (~Filters.command), manage))
dp.add_handler(MessageHandler(Filters.private, start))

def isReady(subscriber):
    return dbu.get(subscriber) + m_interval < time.time() # *60

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
                try:
                    updater.bot.delete_message(chat_id = subscriber, message_id = cache[item])
                except:
                    continue
            cache[item] = msg.forward(chat_id).message_id
            dbu.setTime(chat_id)
        except Exception as e:
            if set(e) != 'Message to forward not found':
                print(e)
                tb.print_exc()
                updater.bot.send_message(chat_id=debug_group, text=str(e))
                queue_to_push_back.append(item)
    for item in queue_to_push_back:
        queue.append(item)

def loop():
    try:
        loopImp()
    except Exception as e:
        print(e)
        tb.print_exc()
        try:
            updater.bot.send_message(chat_id=debug_group, text=str(e))
        except:
            pass
    threading.Timer(m_interval, loop).start() # *60

threading.Timer(1, loop).start()

def manualAdd(subscriber, chat_id):
    msg = updater.bot.send_message(chat_id = subscriber, text = 'test')
    msg.delete()
    chat = getChat(chat_id, msg)
    if not chat:
        return
    r = dbs.add(msg.chat_id, chat.to_dict())
    autoDestroy(msg.reply_text(r, quote=False))
    return

old_config = {
  "-1001484241754": [
    {
      "to": -1001197970228
    }
  ], 
  "-1001445981123": [
    {
      "to": -1001197970228
    }
  ], 
  "-1001419508192": [
    {
      "to": -1001197970228
    }
  ], 
  "-1001414226421": [
    {
      "to": -1001197970228
    }
  ], 
  "-1001409716127": [
    {
      "to": -1001197970228
    }
  ], 
  "-1001402599670": [
    {
      "to": -1001414226421
    }, 
    {
      "to": -1001197970228
    }, 
    {
      "to": -1001409716127
    }
  ], 
  "-1001357677191": [
    {
      "to": -1001198682178
    }
  ], 
  "-1001341438972": [
    {
      "to": -1001197970228
    }
  ], 
  "-1001251820947": [
    {
      "to": -1001197970228
    }
  ], 
  "-1001241147938": [
    {
      "to": -1001197970228
    }, 
    {
      "to": -1001414226421
    }
  ], 
  "-1001187025732": [
    {
      "to": -1001414226421
    }, 
    {
      "to": -1001197970228
    }
  ], 
  "-1001100334908": [
    {
      "to": -1001197970228
    }
  ]
}

for chat_id in old_config:
    print('here')
    for item in old_config[chat_id]:
        subscriber = int(item['to'])
        manualAdd(subscriber, int(chat_id))

updater.start_polling()
updater.idle()