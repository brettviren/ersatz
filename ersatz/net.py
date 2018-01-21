#!/usr/bin/env python
'''
An ersatz "network" that transmits messages through a model for latency and bandwidth.
'''

import simpy
from collections import namedtuple

               
def Message(src, dst, size, **kwds):
    """A network message.  Source and destination addresses must be
    hashable and an (ersatz) size assumed to be in bits.  These and
    any keywords become attributes of the message.
    """
    keys = ['src','dst','size'] + list(kwds.keys())
    return namedtuple('Message',keys)(src=src, dst=dst, size=size, **kwds)

class Pipeline(object):
    '''A host process which runs a sequence of message processing functions.

    The pipeline is a sequence of callables taking a message and a set
    of keyword arguments and returning a new message.  Callables are
    chained through these messages.

    '''
    def __init__(self, funcs, **kwds):
        self.pipeline = funcs
        pass
    def __call__(self, rx, tx):
        while True:
            msg = yield rx.get()
            print ('Pipeline got: %s' % str(msg))
            for func in self.pipeline:
                msg = func(msg)
            print ('Pipeline put: %s' % str(msg))
            yield tx.put(msg)

class Sink(object):
    '''A host which consumes messages via function returning nothing.
    '''
    def __init__(self, func, **kwds):
        self.func = func
        pass
    def __call__(self, rx, tx):
        while True:
            msg = yield rx.get()
            print ('Pipeline got: %s' % str(msg))
            self.func(msg)
            
class Generator(object):
    '''A host process that runs a function and sends returned messages to tx.'''
    def __init__(self, func, **kwds):
        self.func = func
    def __call__(self, rx, tx):
        while True:
            if hasattr(self.func, 'prepare'):
                yield self.func.prepare()
            yield tx.put(self.func())

class Host(object):
    def __init__(self, env, ident, proc=None, rx = None, tx=None):
        self.ident = ident
        self._rx = rx or simpy.Store(env, capacity=1)
        self._rxlock = simpy.Resource(env, 1)
        self._tx = tx or simpy.Store(env, capacity=1)
        self._txlock = simpy.Resource(env, 1)
        if proc:
            env.process(proc(self._rx, self._tx))
        
    def rxlock(self):
        return self._rxlock.request()

    def txlock(self):
        return self._txlock.request()

    def get(self):
        return self._tx.get()

    def put(self, msg):
        return self._rx.put(msg)


def identdictify(things):
    if type(things) is list:
        return {t.ident:t for t in things}
    return things

def switch(env, hosts, delay=0.0, bandwidth=None):
    "Full-duplex switching between hosts"

    hosts = identdictify(hosts)

    def route(host):
        while True:
            with host.txlock() as txlock:
                yield txlock
                msg = yield host.get()
                try:
                    remote = hosts[msg.dst]
                except KeyError:
                    print('Unknown dest host "%s" from "%s".  Know: %s' %
                          (msg.dst, msg.src, ', '.join([h.ident for h in hosts])))
                    continue
                with remote.rxlock() as rxlock:
                    yield rxlock
                    latency = delay
                    if bandwidth:
                        latency += msg.size/bandwidth
                    yield env.timeout(latency)
                    yield remote.put(msg)

    for h in hosts.values():
        env.process(route(h))


def router(env, fromhosts, tohosts, delay=0.0, bandwidth=None):
    "Route packets from fromhosts to tohosts"
    fromhosts = identdictify(fromhosts)
    tohosts = identdictify(tohosts)

    def route(host):
        while True:
            with host.txlock() as txlock:
                yield txlock
                msg = yield host.get()
                try:
                    remote = tohosts[msg.dst]
                except KeyError:
                    print('Unknown dest host "%s" from "%s".  Know: %s' %
                          (msg.dst, msg.src, ', '.join([h.ident for h in tohosts])))
                    continue
                with remote.rxlock() as rxlock:
                    yield rxlock
                    latency = delay
                    if bandwidth:
                        latency += msg.size/bandwidth
                    yield env.timeout(latency)
                    yield remote.put(msg)

    for h in fromhosts.values():
        env.process(route(h))
        


class Pipe(object):
    """
    A true fixed size store.

    tx = yield pipe.send()
    tx.put(msg)

    rx = yield pipe.recv()
    msg = rx.get()

    """
    def __init__(self, env, delay=0.0, bandwidth=None,
                 tx = None, rx = None):
        self.env = env
        self.delay = delay
        self.bandwidth = bandwidth
        self.tx = tx or simpy.Store(env, capacity=1)
        self.rx = rx or simpy.Store(env, capacity=1)
        self.tx.put(self)      # ready for transmit
        self.packets = list()

    def send(self):
        return self.tx.get()
    def recv(self):
        return self.rx.get()

    def latency(self, packet):
        delay = self.delay
        if self.bandwidth:
            delay += packet.size/self.bandwidth
        yield self.env.timeout(delay)
        self.packets.append(packet)
        self.rx.put(self)       # ready for receive

    def put(self, packet):
        self.env.process(self.latency(packet))

    def get(self):
        assert (self.packets)
        p = self.packets.pop(0)
        self.tx.put(self)       # ready for next transmit
        return p

class Link(object):
    """
    A Link represents the one-way propagation through a communication
    channel.  Messages put to the link suffer a fixed delay.  No more
    than one message may occupy the link at a time.
    """
    def __init__(self, env, delay=0.0, inspector=None):
        self.env = env
        self.delay = delay
        self.inspector = inspector
        self.pipe = simpy.Store(env, capacity=1)
        self.sem = simpy.Resource(self.env, capacity=1)

    def latency(self, msg):
        with self.sem.request() as request:
            yield request
            yield self.env.timeout(self.delay)
            if self.inspector:
                self.inspector(msg)
            self.pipe.put(msg)        

    def put(self, msg):
        '''
        Put a message to the link.  Caller should yield this to make it blocking.  
        '''
        return self.env.process(self.latency(msg))

    def get(self):
        return self.pipe.get()

def NIC(env, delay=0.0, rxinspector=None, txinspector=None):
    """A symmetric full-duplex network interface controller consiting of
    two one way Link objects.  The links are available from the .rx
    and .tx elements.  These names are from the point of view of the
    host of the NIC.  That is, rx provides incoming packets received
    by the host.

    """
    return namedtuple('NIC','rx tx')(Link(env, delay, rxinspector),
                                     Link(env, delay, txinspector))

class Switch(object):
    """A Switch connects """

    def __init__(self, env, bandwidth=None, inspector=None):
        """Create a switch with unlimited ports and infinite switch fabric bandwidth."""
        self.env = env
        self.bandwidth = bandwidth
        self.inspector = inspector
        self.ports = dict()           # unlimited, keyed by addr

    def transfer(self, src):
        while True:
            msg = yield src.tx.get() # buffers full message
            dst, sem = self.ports[msg.dst]
            with sem.request() as request:
                yield request
                delay = src.tx.delay + dst.rx.delay
                if self.bandwidth:
                    delay += msg.size / self.bandwidth
                yield self.env.timeout(delay)

                if self.inspector:
                    self.inspector(msg)
                dst.rx.put(msg)

    def conn(self, addr, nic):
        """Connect a nic at given address to a switch port.  The nic must have
        .rx and .tx attributes.  Messages go from the nic's tx to 
        another's rx based on the address of the message.
        """ 
        self.ports[addr] = (nic, simpy.Resource(self.env, capacity=1))
        self.env.process(self.transfer(nic))

