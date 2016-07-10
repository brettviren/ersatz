#!/usr/bin/env python3
'''
Test ersatz.node
'''

import simpy
from ersatz.datum import Datum
from ersatz.node import Node

def parse_address(addr):
    name,number = addr.rsplit('.',1)
    return name,int(number)

def form_address(name, number):
    return "%s.%d" % (name, number)

class Splitter(object):
    def __init__(self, latency, rate, number=2):
        self.latency = latency
        self.rate = rate
        self.number = number

    def __call__(self, datum):
        ouraddr = datum.rxaddr
        name,number = parse_address(ouraddr)
        theiraddr = form_address(name, number+1), 
        target_size = datum.size/number

        delay = target_size/self.rate
        payload = datum.payload
        step = int(len(payload) / self.number)

        for count in range(self.number):
            de = self.latency + (count+1)*delay
            pl = payload[step*count:step*(count+1)]
            da = Datum(ouraddr, theiraddr, target_size, pl)
            yield de,da
    

def chirp(datum):
    print ("datum: %s" % datum)
    return

def shunt(env, n1, n2, bandwidth, latency=0.0):
    while True:
        d = yield n1.tx.get()
        d.bandwidth = bandwidth # get whole thing
        wait = d.eta
        yield env.timeout(wait + latency)
        d.update(wait)          # it's a function of switch, not datum
        print ("shunted: t=%.1f %s" % (env.now, d))
        yield n2.rx.put(d)

def test_simple():
    env = simpy.Environment()

    n1 = Node(env, Splitter(10, 100))
    n2 = Node(env, chirp)
    env.process(shunt(env, n1, n2, 10))

    n1.rx.put(Datum("node.1", "node.2", 1000, payload=range(10)))
    env.run(until=200)

if '__main__' == __name__:
    test_simple()
    
