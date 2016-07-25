#!/usr/bin/env python3
'''

Primitive functionality in which a single process in the ersatz graph is run.

'''
import simpy

class Node(object):
    '''
    A Node mediates receiving and transmitting streams of data by
    applying a datum transform function.
    '''

    def __init__(self, env, transform):
        '''
        Create a node.

        @param env: the simpy environment

        @param transform: a function called on each input datum
            returning a collection of output datum.
        @type transform: calable(datum, now) -> [datum,...]
        '''
        self.transform = transform
        self.rx = simpy.Store(env)
        self.tx = simpy.Store(env)
        self.env = env
        self.env.process(self.run())

        
    def output(self, delay, datum):
        yield self.env.timeout(delay)
        yield self.tx.put(datum)

    def run(self):
        '''
        Get rx datum, transform, apply delay and put any tx datum.
        '''
        while True:
            datum = yield self.rx.get()
            dd  = self.transform(datum)
            if not dd:
                continue
            for delay, datum in dd:
                #print ('node: delay=%.1f datum=%s' % (delay, datum))
                self.env.process(self.output(delay, datum))
