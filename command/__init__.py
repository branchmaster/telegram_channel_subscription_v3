from telegram_util import splitCommand, autoDestroy, getChat

def formatSubscription(s):
    return '[' + s['title'] + '](t.me/' + str(s.get('username')) + ')'

def handleCommand(update, context, dbs):
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
        chat = getChat(context.bot, text)
        if not chat:
            return
        r = dbs.add(msg.chat_id, chat.to_dict())
        autoDestroy(msg.reply_text(r, quote=False))
        return
    if 'all' in command:
        for reciever in dbs.getAll():
            if int(reciever) != msg.chat_id:
                msg.reply_to_message.forward(reciever)
        return