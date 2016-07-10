#!/usr/bin/env python3

import simpy
from ersatz.switch import Switch, LinkedSwitch
from ersatz.datum import Datum
from ersatz.monitoring import trace

def test_balance():
    sw = Switch(None, 100)
    for ip in range(5):
        for op in range(max(0,ip-2),min(5,ip+2)):
            sw.stage(Datum(ip, op, 10, None))
    
    imb,count = sw.balance()
    print ('%d iters: max adj: %.1f' % (count, imb))
    sw.dump()

    with open('test_balance.dot','w') as fp:
        fp.write(sw.dot())

    

def slurp(env, outbox):
    while True:
        datum = yield outbox.get()
        print ('final: %s' % datum)
        print ('\tDONE: at %.1f, %s' % \
               (env.now, datum.payload))
        print('\t    : %s -> %s' % (datum.txaddr, datum.rxaddr))

def add_stream(env, inbox, wait, txaddr, rxaddr, size, payload):
    print ('waiting %f to start stream of "%s"' % (wait, payload))
    yield env.timeout(wait)
    print ('starting stream with payload "%s"' % payload)
    yield inbox.put(Datum(txaddr, rxaddr, size, payload))

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
    env.process(add_stream(env, sw.inbox, 0, 'p1', 'p2', 50, "datum1"))
    env.process(add_stream(env, sw.inbox, 2, 'p1', 'p3', 50, "datum2"))
    env.process(add_stream(env, sw.inbox, 4, 'p2', 'p3', 50, "datum3"))

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
