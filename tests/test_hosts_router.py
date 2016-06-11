#!/usr/bin/env python

import simpy
from ersatz.net import Message, Host, switch
from ersatz import units


def dump(env, me, msg):
    print ('%6.1f\t%s:\t%s' % (env.now, me, msg))

class RR(object):
    def __init__(self, env):
        self.env = env
    def __call__(self, rx, tx):
        me = 'h1'
        dsts = ['h2','h3']
        count = 0
        while True:
            dst = dsts[count%len(dsts)]
            msg = yield rx.get()
            newmsg = Message(me, dst, units.GB, count=count, oldcount=msg.count)
            dump(self.env, 'rr', newmsg)
            yield tx.put(newmsg)
            count += 1

class Chirp(object):
    def __init__(self, env):
        self.env = env

    def __call__(self, rx,tx):
        while True:
            msg = yield rx.get()
            dump(self.env, 'chirp', msg)


class MessageGenerator(object):
    def __init__(self, env):
        self.env = env
    def __call__(self, rx,tx):
        me = 'h3'
        dsts = ['h4','h5']
        count = 0;
        while True:#for count in range(10):
            dst = dsts[count%len(dsts)]
            yield self.env.timeout(10)
            newmsg = Message(me, dst, units.GB, count=count, )
            dump(self.env, 'gen', newmsg)
            yield tx.put(newmsg)
            count += 1

def message_injector(env, host):
    for count  in range(5):
        yield env.timeout(units.second)
        msg = Message(None, host.ident,
                      3*units.GB, sent=env.now, count=count)
        with host.rxlock() as lock:
            yield lock
            dump(env, "inject", msg)
            yield host.put(msg)
    for count in range(5):
        yield env.timeout(100)


def test_graph():
    
    env = simpy.Environment()

    h1 = Host(env, 'h1', proc=RR(env))
    h2 = Host(env, 'h2', proc=Chirp(env))
    h3 = Host(env, 'h3', proc=MessageGenerator(env))
    h4 = Host(env, 'h4', proc=Chirp(env))
    h5 = Host(env, 'h5', proc=Chirp(env))
    all_hosts = [h1, h2, h3, h4, h5]
    switch(env, all_hosts)

    env.process(message_injector(env, h1))



    SIM_DURATION = 100
    env.run(until=SIM_DURATION)

if '__main__' == __name__:
    test_graph()
