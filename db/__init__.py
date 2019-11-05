import traceback as tb
import yaml
import time

class DB(object):
    def __init__(self):
        try:
            with open('db.yaml') as f:
                self.DB = yaml.load(f, Loader=yaml.FullLoader)
        except Exception as e:
            print(e)
            tb.print_exc()
            self.DB = {}

    def getList(self, chat_id):
        return self.DB.get(chat_id, [])

    def deleteIndex(self, chat_id, index):
        try:
            del self.DB[chat_id][index]
            self.save()
            return 'success'
        except Exception as e:
            return str(e)

    def setTime(self, chat_id):
        self.DB[chat_id]['last_update'] = time.time()
        self.save()

    def add(self, chat_id, chat):
        self.DB[chat_id] = self.DB.get(chat_id, [])
        if chat['id'] in [x['id'] for x in self.DB[chat_id]]:
            return 'FAIL: subscripion already exist.'
        self.DB[chat_id].append(chat)
        self.save()
        return 'success'

    def save(self):
        with open('db.yaml', 'w') as f:
            f.write(yaml.dump(self.DB, sort_keys=True, indent=2))