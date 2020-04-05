import time
import yaml
import os
import sys

if 'test' in str(sys.argv):
    HOUR = 20
else:
    HOUR = 60 * 60

class HOLD(object):
    def __init__(self):
        self.holds = {}

    def hold(self, x, msg=None, hold_hour = 1):
        self.holds[x] = self.holds.get(x, [])
        self.holds[x].append((time.time() + hold_hour * HOUR, msg))

    def onHold(self, x):
        return not not self.holds.get(x)

    def clearHold(self, debug_group):
        for x in list(self.holds.keys()):
            while self.holds[x]:
                t, msg = self.holds[x].pop()
                if t < time.time():
                    continue
                if msg:
                    try:
                        r = msg.forward(debug_group.id)
                        r.delete()
                    except Exception as e:
                        continue
                self.holds[x].append((t, msg))
                break

class CACHE(object):
    def __init__(self):
        self.cache = set()

    def add(self, x):
        if x in self.cache:
            return False
        self.cache.add(x)
        return True

def getSenderDict(chat):
    if chat.username:
        return {
            'id': chat.id,
            'username': chat.username,
        }
    return {
        'id': chat.id,
        'title': chat.title,
    }


class QUEUE(object):
    def __init__(self):
        try:
            with open('queue.yaml') as f:
                self.queue = yaml.load(f, Loader=yaml.FullLoader)
        except FileNotFoundError as e:
            self.queue = []

    def append(self, x):
        self.queue.append(x)
        self.save()

    def replace(self, x):
        self.queue = x
        self.save()

    def pop(self):
        x = self.queue.pop()
        return x

    def pop_all(self, a, b, d):
        r = [x[2] for x in self.queue if x[0] == a and x[1] == b and x[3] == d]
        self.queue = [x for x in self.queue if not (x[0] == a and x[1] == b and x[3] == d)]
        self.save()
        return r

    def empty(self):
        return len(self.queue) == 0

    def save(self):
        with open('queue_tmp.yaml', 'w') as f:
            f.write(yaml.dump(self.queue, sort_keys=True, indent=2))
        os.system('mv queue_tmp.yaml queue.yaml')

    def getHoldHour(self, reciever):
        r = [x[3] if x[3] else (x[1], x[2]) for x in self.queue if x[0] == reciever]
        waiting = len(set(r)) + 1.0
        return min(5, 24.0 / waiting)

class SUBSCRIPTION(object):
    def __init__(self):
        try:
            with open('subscription.yaml') as f:
                self.SUBSCRIPTION = yaml.load(f, Loader=yaml.FullLoader)
        except FileNotFoundError as e:
            self.SUBSCRIPTION = {}

    def getList(self, chat_id):
        return self.SUBSCRIPTION.get(chat_id, [])

    def getAll(self):
        # only non-channel group and channels
        r = set()
        for x in self.SUBSCRIPTION:
            try: # not tested yet
                channel = msg.bot.get_chat(x)
                if x.type == 'channel':
                    r.add(x)
            except:
                pass
            for y in self.SUBSCRIPTION[x]:
                r.add(y['id'])
        return r

    def deleteIndex(self, chat_id, index):
        try:
            del self.SUBSCRIPTION[chat_id][index]
            self.save()
            return 'success'
        except Exception as e:
            return str(e)

    def getSubsribers(self, chat_id):
        result = []
        for subscriber, items in self.SUBSCRIPTION.items():
            for item in items:
                if item['id'] == chat_id:
                    result.append(subscriber)
                    break
        return result

    def record(self, chat):
        if not chat.id in self.SUBSCRIPTION:
            self.SUBSCRIPTION[chat.id] = []
            self.save()

    def add(self, reciever, sender):
        self.SUBSCRIPTION[reciever.id] = self.SUBSCRIPTION.get(reciever.id, [])
        if sender.id in [x['id'] for x in self.SUBSCRIPTION[reciever.id]]:
            return 'FAIL: subscripion already exist.'
        self.SUBSCRIPTION[reciever.id].append(getSenderDict(sender))
        self.save()
        return 'success'

    def save(self):
        with open('subscription.yaml', 'w') as f:
            f.write(yaml.dump(self.SUBSCRIPTION, sort_keys=True, indent=2))