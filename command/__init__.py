from telegram_util import splitCommand, autoDestroy, getChat, formatChat

forward_all_record = {}

def handleCommand(update, context, dbs):
    msg = update.effective_message
    autoDestroy(msg)
    command, text = splitCommand(msg.text)
    if 's3_l' in command:
        subscriptions = dbs.getList(msg.chat_id)
        subscriptions = [str(index) + ': ' + \
            formatChat(context.bot, x['id']) for \
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
        r = dbs.add(msg.chat, chat)
        autoDestroy(msg.reply_text(r, quote=False))
        return
    if 'all' in command:
        global forward_all_record
        # untested code
        to_forward = msg.reply_to_message
        key = (to_forward.chat_id, to_forward.message_id)
        if key not in forward_all_record:
            forward_all_record[key] = []
        for reciever in dbs.getAll():
            if int(reciever) != msg.chat_id:
                print(to_forward)
                print(to_forward.caption_markdown)
                print(to_forward.caption)
                return
                if to_forward.text_markdown:
                    r = msg.bot.send_message(reciever, to_forward.text_markdown, 
                        parse_mode='Markdown')
                elif to_forward.photo:
                    r = msg.bot.send_photo(reciever, to_forward.photo[-1].file_id, 
                        cap=to_forward.photo[-1].caption_markdown, parse_mode='Markdown')
                else:
                    r = to_forward.forward(reciever)
                forward_all_record[key].append(r)
        return
    if 'delete' in command:
        to_delete = msg.reply_to_message
        key = (to_delete.chat_id, to_delete.message_id)
        for r in forward_all_record[key]:
            try:
                r.delete()
            except:
                pass
