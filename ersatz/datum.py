#!/usr/bin/env python3
'''
A datum (singular) is an atomic unit of data which exists between a
producer/transmitter and a consumer/receiver.  
'''

class Datum(object):
    '''
    A Datum object holds ersatz system bookkeeping for transmitting a
    payload between two endpoints.
    '''

    eps = 1.0e-9

    def __init__(self, txaddr, rxaddr, size, payload=None):
        '''
        Create a datum.

        @param txaddr: address of the transmitter of the datum.
        @type txaddr: hashable

        @param rxaddr: address of the receiver of the datum.
        @type rxaddr: hashable

        @param size: size of the datum used to determine bandwidth
            related transmission delay.
        @type size: number

        @param payload: the semantic contents of the datum
        @type payload: opaque
        '''
        self.txaddr = txaddr
        self.rxaddr = rxaddr
        self.size = size
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
        Return time to complete transfer of the datum at current bandwidth.
        '''
        try:
            t = self.remaining / self.bandwidth
        except ZeroDivisionError:
            print ("zero bandwidth: %s -> %s size=%f remaining=%f" % (self.txaddr, self.rxaddr, self.size, self.remaining))
            raise
        if t<0 and t > -self.eps:
            t = 0;
        return t

    def __lt__(self, other):
        if self.remaining < other.remaining: return True
        if self.size < other.size: return True
        return id(self) < id(other)

    def __str__(self):
        return 'datum %s --> %s remaining: %.1f/%.1f (%.2f%%) bw=%.1f pl=%s' % \
            (self.txaddr, self.rxaddr, self.remaining, self.size,
             100.0*self.remaining/self.size, self.bandwidth, self.payload)

