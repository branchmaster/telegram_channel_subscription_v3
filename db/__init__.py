import traceback as tb
import yaml
import time

class UPDATE_TIME(object):
    def __init__(self):
        try:
            with open('update_time.yaml') as f:
                self.UPDATE_TIME = yaml.load(f, Loader=yaml.FullLoader)
        except Exception as e:
            print(e)
            tb.print_exc()
            self.UPDATE_TIME = {}

    def setTime(self, chat_id):
        self.UPDATE_TIME[chat_id] = time.time()
        self.save()

    def save(self):
        with open('update_time.yaml', 'w') as f:
            f.write(yaml.dump(self.UPDATE_TIME, sort_keys=True, indent=2))

class SUBSCRIPTION(object):
    def __init__(self):
        try:
            with open('subscription.yaml') as f:
                self.SUBSCRIPTION = yaml.load(f, Loader=yaml.FullLoader)
        except Exception as e:
            print(e)
            tb.print_exc()
            self.SUBSCRIPTION = {}

    def getList(self, chat_id):
        return self.SUBSCRIPTION.get(chat_id, [])

    def deleteIndex(self, chat_id, index):
        try:
            del self.SUBSCRIPTION[chat_id][index]
            self.save()
            return 'success'
        except Exception as e:
            return str(e)

    def getSubsribers(self, chat_id):
        result = []
        for subscriber, items in enumerate(self.SUBSCRIPTION):
            for item in items:
                if item['id'] == chat_id:
                    result.append(subscriber)
                    break
        return result

    def add(self, chat_id, chat):
        self.SUBSCRIPTION[chat_id] = self.SUBSCRIPTION.get(chat_id, [])
        if chat['id'] in [x['id'] for x in self.SUBSCRIPTION[chat_id]]:
            return 'FAIL: subscripion already exist.'
        self.SUBSCRIPTION[chat_id].append(chat)
        self.save()
        return 'success'

    def save(self):
        with open('subscription.yaml', 'w') as f:
            f.write(yaml.dump(self.SUBSCRIPTION, sort_keys=True, indent=2))