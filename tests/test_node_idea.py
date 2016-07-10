import simpy
from ersatz import units
from ersatz.net import Message

class ExclusiveQueue(object):
    def __init__(self, env, ident):
        self.env = env
        self.ident = ident
        self.lock = simpy.Resource(env, 1)
        self.queue = simpy.Store(env)

    def put(self, msg):
        return self.env.process(self._put(msg))

    def _put(self, msg):
        with self.lock.request() as req:
            yield req
            self.env.timeout(1)
            print ('%s: t=%.1f putting %s' % (self.ident, self.env.now, msg))
            self.queue.put(msg)
            self.env.timeout(1)



class Node(object):
    def __init__(self, env, ident):
        self.env = env
        self.ident = ident

        self.in_queue = ExclusiveQueue(env,"i"+ident[-1])
        self.out_queue = ExclusiveQueue(env,"o"+ident[-1])

        env.process(self.run())

    def run(self):
        while True:
            msg = yield self.in_queue.queue.get()
            yield self.env.timeout(2*units.second)
            print ('%s: t=%.1f processing %s' % (self.ident, self.env.now, msg))
            self.out_queue.queue.put(msg)


    # def put(self, msg):
    #     with self.write_lock.request() as req:
    #         yield req
    #         print ('putting %s' % msg)
    #         self.in_queue.put(msg)

    # def get(self):
    #     with self.read_lock.request() as req:
    #         yield req
    #         return self.out_queue.get()


def sender(env, node, me):
    for count in range(5):
        yield env.timeout(units.second)
        msg = Message(None, None, units.GB, sent=env.now, count=count)
        print ('%s: t=%.1f sending %s' % (me, env.now, msg))
        #node.in_queue.put(msg)
        node.in_queue.put(msg)

def receiver(env, node, me):
    while True:
        with node.out_queue.lock.request():
            msg = yield node.out_queue.queue.get()
            print ('%s: t=%.1f got %s' % (me, env.now, msg))

def test_sender_receiver():

    env = simpy.Environment()
    node = Node(env, "n1")
    env.process(sender(env, node, "s1"))
    env.process(sender(env, node, "s2"))
    env.process(receiver(env, node, "r1"))
    SIM_DURATION = 100
    env.run(until=SIM_DURATION)

if '__main__' == __name__:
    test_sender_receiver()
    
