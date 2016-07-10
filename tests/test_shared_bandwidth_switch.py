#!/usr/bin/env python3

import simpy
from ersatz.switch import Switch, LinkedSwitch
from ersatz.stream import Stream
from ersatz.monitoring import trace

def test_balance():
    sw = Switch(None, 100)
    for ip in range(5):
        for op in range(max(0,ip-2),min(5,ip+2)):
            sw.stage(Stream(ip, op, 10))
    
    imb,count = sw.balance()
    print ('%d iters: max adj: %.1f' % (count, imb))
    sw.dump()

    with open('test_balance.dot','w') as fp:
        fp.write(sw.dot())

    

def slurp(env, outbox):
    while True:
        stream = yield outbox.get()
        print ('final: %s' % stream)
        dt = env.now-stream.start
        print ('\tDONE: at %.1f took %.1f avg bandwidth=%f %s' % \
               (env.now, dt, stream.size/dt, stream.payload))
        print('\t    : %s -> %s' % (stream.txaddr, stream.rxaddr))

def add_stream(env, inbox, wait, txaddr, rxaddr, size, payload):
    print ('waiting %f to start stream "%s"' % (wait, payload))
    yield env.timeout(wait)
    print ('starting stream "%s"' % payload)
    yield inbox.put(Stream(txaddr, rxaddr, size, env.now, payload))

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
    env.process(slurp(env, sw.outbox))
    env.process(add_stream(env, sw.inbox, 0, 'p1', 'p2', 50, "stream1"))
    env.process(add_stream(env, sw.inbox, 2, 'p1', 'p3', 50, "stream2"))
    env.process(add_stream(env, sw.inbox, 4, 'p2', 'p3', 50, "stream3"))

    env.run(until=200)
    
#    for item in monitor.data:
#        print (str(item))

def test_linked():
    env = simpy.Environment()

    nic1_addr = 'nic1'
    nic1_tx = simpy.Store(env)
    nic2_addr = 'nic2'
    nic2_rx = simpy.Store(env)

    env.process(add_stream(env, nic1_tx, 2, nic1_addr, nic2_addr, 50, "hello world"))
    env.process(slurp(env, nic2_rx))

    lsw = LinkedSwitch(env, 10)
    print ("Linking nic1")
    lsw.link_nic(nic1_addr, None, nic1_tx)
    print ("Linking nic2")
    lsw.link_nic(nic2_addr, nic2_rx, None)
    print ("running")
    env.run(until=200)


if '__main__' == __name__:
    test_balance()
    test_switching()
    test_linked()
