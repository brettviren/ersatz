#!/usr/bin/env python3

import simpy
from ersatz.switch import Switch, Stream
from ersatz.monitoring import trace

def test_balance():
    sw = Switch(None, 100)
    for ip in range(5):
        for op in range(max(0,ip-2),min(5,ip+2)):
            sw.stage(Stream(ip,op, 10))
    
    imb,count = sw.balance()
    print ('%d iters: max adj: %.1f' % (count, imb))
    sw.dump()

    with open('test_balance.dot','w') as fp:
        fp.write(sw.dot())

    

def slurp(env, sw):
    while True:
        stream = yield sw.outbox.get()
        print ('final: %s' % stream)
        dt = env.now-stream.start
        print ('\tDONE: at %.1f took %.1f avg bandwidth=%f %s' % \
               (env.now, dt, stream.size/dt, stream.payload))

def add_stream(env, sw, wait, inp, outp, size, payload):
    print ('waiting %f to start stream "%s"' % (wait, payload))
    yield env.timeout(wait)
    print ('starting stream "%s"' % payload)
    yield sw.inbox.put(Stream(inp, outp, size, env.now, payload))

class FillData(object):
    def __init__(self):
        self.data = list()
    def __call__(self, t, prio, eid, event):
        self.data.append((t, prio, eid, event))

def test_switching():
    env = simpy.Environment()

    monitor = FillData()
    trace(env, monitor)

    sw = Switch(env, 10)
    env.process(slurp(env, sw))
    env.process(add_stream(env, sw, 0, 'p1', 'p2', 50, "stream1"))
    env.process(add_stream(env, sw, 2, 'p1', 'p3', 50, "stream2"))
    env.process(add_stream(env, sw, 4, 'p2', 'p3', 50, "stream3"))

    env.run(until=200)
    
#    for item in monitor.data:
#        print (str(item))


if '__main__' == __name__:
    test_balance()
    test_switching()
    
