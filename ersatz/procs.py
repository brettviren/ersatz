#!/usr/bin/env python

class Pipeline(object):
    '''A host process which runs a sequence of message processing functions.

    The pipeline is a sequence of callables taking a message and a set
    of keyword arguments and returning a new message.  Callables are
    chained through these messages.

    '''
    def __init__(self, env, name, cfg, **kwds):
        self.env = env
        self.params = kwds
        pass
    def __call__(self, rx, tx):
        while True:
            msg = yield rx.get()
            for proc in pipeline:
                msg = proc(msg)

            newmsg = Message(me, dst, units.GB, count=count, oldcount=msg.count)
            dump(self.env, 'rr', newmsg)
            yield tx.put(newmsg)
            count += 1

        pass

class Collate(object):
    '''
    A process that routes its messages to a 
    '''

    def __init__(self, env, host, **kwds):
        self.env = env
        self.host = host

