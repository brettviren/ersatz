#!/usr/bin/env python3
'''
An ersatz node groups together an input message queue, a message
processing service and a collection of output queues (which are the
input queues of other nodes).
'''

import simpy
class Node(object):
    '''
    A node manages the execution of a number of service instances on a
    queue of inputs.
    '''
    def __init__(self, env, queue, service, outs=None, nservices=1, **service_kwds):
        '''
        Create a Node.

        @param env: a simpy Environment
        @param queue: a simpy Store
        @param service: a generator yielding simpy events, taking a packet and a list of queues.
        @param outs: an ordered dictionary of queues.
        @param nservices: the number of concurrent services that may be active.
        '''
        self.env = env
        self.queue = queue
        self.service = service
        self.service_kwds = service_kwds
        self.service_lock = simpy.Resource(env, nservices)
        self.outs = outs or list()
        self.action = self.env.process(self.run())

    def run(self):
        while True:
            req = self.service_lock.request()
            yield req
            packet = None
            if self.queue:
                packet = yield self.queue.get()
            self.env.process(self.call_service(req, packet))

    def call_service(self, req, packet):
        for evt in self.service(self.env, packet, self.outs, **self.service_kwds):
            yield evt
        self.service_lock.release(req)


