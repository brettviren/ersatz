#!/usr/bin/env python3
'''
'''

class Stream(object):
    '''
    A stream represents the transfer of one datum across some link.
    '''
    def __init__(self, txaddr, rxaddr, size, now=None, payload=None):
        '''
        Create a stream.

        @param txaddr: address of the transmitter of the stream.
        @type txaddr: hashable

        @param rxaddr: address of the receiver of the stream.
        @type rxaddr: hashable

        @param size: size of the transfer
        @type size: number

        @param now: the time the stream was initiated
        @type now: number

        @param payload: the semantic contents of the stream
        @type payload: opaque
        '''
        self.txaddr = txaddr
        self.rxaddr = rxaddr
        self.size = size
        self.start = now
        self.payload = payload        

        self.remaining = size
        self.bandwidth = 0

    def update(self, elapsed):
        '''
        Update remaining assuming elapsed time since last update.
        '''
        self.remaining -= self.bandwidth*elapsed

    @property
    def eta(self):
        '''
        Return time to complete stream at current bandwidth.
        '''
        return self.remaining / self.bandwidth

    def __lt__(self, other):
        if self.remaining < other.remaining: return True
        if self.size < other.size: return True
        if self.start < other.start: return True
        return id(self) < id(other)

    def __str__(self):
        return 'stream %s --> %s start at %d, remaining: %.1f/%.1f (%.2f%%) bw=%.1f' % \
            (self.txaddr, self.rxaddr, self.start, self.remaining, self.size,
             100.0*self.remaining/self.size, self.bandwidth)

