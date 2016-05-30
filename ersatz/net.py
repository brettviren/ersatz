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


def router(env, hosts, delay=0.0, bandwidth=None):
    if type(hosts) is list:
        remotes = {h.ident:h for h in hosts}

    def route(host):
        while True:
            with host.txlock() as txlock:
                yield txlock
                msg = yield host.get()
                remote = remotes[msg.dst]
                with remote.rxlock() as rxlock:
                    yield rxlock
                    latency = delay
                    if bandwidth:
                        latency += msg.size/bandwidth
                    yield env.timeout(latency)
                    yield remote.put(msg)

    for h in hosts:
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
    """A Link represents the one-way propagation through a communication
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
        self.env.process(self.latency(msg))

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

