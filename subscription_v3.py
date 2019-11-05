#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import yaml
import time
from telegram.ext import Updater, MessageHandler, Filters
from db import DB
import threading
import traceback as tb

START_MESSAGE = ('''
Channel Subscription for channels and groups. Bot needs to be in the subscribed channel.
''')

db = DB()

with open('CREDENTIALS') as f:
    CREDENTIALS = yaml.load(f, Loader=yaml.FullLoader)

with open('config') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

test_channel = -1001459876114
debug_group = CREDENTIALS.get('debug_group') or -1001198682178

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
        print(command, text)
        if 's3_l' in command:
            print('here')
            subscriptions = db.getList(msg.chat_id)
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
            r = db.deleteIndex(msg.chat_id, index)
            autoDestory(msg.reply_text(r, quote = False))
            return
        if 's3_s' in command:
            chat = getChat(text, msg)
            if not chat:
                return
            r = db.add(msg.chat_id, chat.to_dict())
            autoDestory(msg.reply(r, quote=False))
            return
    except Exception as e:
        updater.bot.send_message(chat_id=debug_group, text=str(e)) 
        print(e)
        tb.print_exc()

def manage(update, context):
    try:
        msg = update.message
        if (not msg) or (not isMeaningful(msg)):
            return 
        chat_id = msg.chat_id
        if not chat_id or chat_id > 0:
            return
        db.setTime(chat_id)
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

updater.start_polling()
updater.idle()