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
        return self.DB[chat_id]

    def deleteIndex(self, chat_id, index):
        del self.DB[chat_id][index]
        self.save()

    def setTime(self, chat_id):
        self.DB[chat_id]['last_update'] = time.time()
        self.save()

    def save(self):
        with open('db.yaml', 'w') as f:
            f.write(yaml.dump(self.DB, sort_keys=True, indent=2))