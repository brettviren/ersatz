#!/usr/bin/env python3
'''
Simulate a comm link with bandwidth shared by multiple streams.
'''

import simpy

class Stream(object):
    def __init__(self, ident, size, now):
        self.ident = ident
        self.size = size
        self.remaining = size
        self.start = now
    def __str__(self):
        return 'stream "%s" start at %d, remaining: %.1f/%.1f (%.2f%%)' % (self.ident, self.start, self.remaining, self.size, 100.0*self.remaining/self.size)


class Link(object):
    def __init__(self, env, bandwidth):
        self.env = env
        self.streams = dict()
        self.bandwidth = bandwidth
        self.inbox = simpy.Store(env) # streams start
        self.outbox = simpy.Store(env) # streams finish
        self.transmit = simpy.PreemptiveResource(env, capacity=1)
        env.process(self.accept())


    def accept(self):
        while True:
            stream = yield self.inbox.get()
            print ('accept with %d ongoing:  %s' % (len(self.streams), stream))
            self.env.process(self.deliver(stream))

    def deliver(self, stream):
        self.streams[stream.ident] = stream
        nstreams = len(self.streams)
        bandwidth = self.bandwidth / nstreams
        eta = stream.remaining / bandwidth
        prio = -1*nstreams
        with self.transmit.request(priority=prio) as req:
            yield req
            start = self.env.now
            try:
                print ('delivery with prio %d, bw %.1f, eta in %.1f: %s' % (prio, bandwidth, eta, stream))
                yield self.env.timeout(eta)
            except simpy.Interrupt as interrupt:
                # update stream state
                #dt = self.env.now - interrupt.cause.usage_since
                dt = self.env.now - start
                stream.remaining -= dt*bandwidth
                self.streams.pop(stream.ident)
                print ('interupted at %.1f after %.1f with %s' % (self.env.now, dt, stream))
                self.inbox.put(stream)
                return

            dt = self.env.now - start
            stream.remaining -= dt*bandwidth
            self.streams.pop(stream.ident)
            print ('delivered %s' % stream)
            yield self.outbox.put(stream)

def slurp(env, link):
    while True:
        stream = yield link.outbox.get()
        print ('final: %s' % stream)
        dt = env.now-stream.start
        print ('\ttook %.1f avg bandwidth=%f' % (dt, stream.size/dt))

def add_stream(env, link, wait, ident, size):
    print ('waiting %f to start stream "%s"' % (wait, ident))
    yield env.timeout(wait)
    print ('starting stream "%s"' % ident)
    yield link.inbox.put(Stream(ident, size, env.now))

def test_it():
    env = simpy.Environment()
    link = Link(env, 10)
    
    env.process(slurp(env, link))
    env.process(add_stream(env, link, 0, 'a', 50))
    env.process(add_stream(env, link, 2, 'b', 50))
    env.process(add_stream(env, link, 4, 'c', 50))

    env.run(until=100)

if '__main__' == __name__:
    test_it()
    
