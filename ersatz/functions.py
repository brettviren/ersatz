'''

Message processing functions.

'''
from collections import namedtuple

from ersatz.util import unitify
from ersatz.net import Message

class generate(object):
    def __init__(self, src='', dst='', size='', **kwds):
        if not size or not src or not dst:
            raise ValueError('generate needs a src, dst and size')
        self.dat = dict(size= unitify(size),
                        src = src,
                        dst = dst, **kwds)
    def __call__(self):
        d = dict()
        #d.update(**{f:getattr(msg,f) for f in msg._fields})
        d.update(**self.dat)
        msg = Message(**d)
        print('generate: %s' % str(msg))
        return msg


class roundrobin(object):
    "Pick a destination based on a round robin count"
    Dat = namedtuple('RoundRobin','sequence_key number_dst pattern_dst')
    def __init__(self, **kwds):
        self.dat = self.Dat(**{k:kwds[k] for k in self.Dat._fields})
    def __call__(self, msg):
        seqno = int(getattr(msg, self.dat.sequence_key))
        ind = seqno%int(self.dat.number_dst)
        dst = self.dat.pattern_dst%ind
        return msg._replace(dst=dst)
        

class compress(object):
    "Reduce the size of the object"
    def __init__(self, factor=None, **kwds):
        self.factor = int(factor)
    def __call__(self, msg):
        return msg._replace(size = msg.size / self.factor)

class dumpmsg(object):
    "Dump the messages it gives using the provided message template."
    def __init__(self, env, template="", **kwds):
        self.env = env
        self.template = template
        self.kwds = kwds
    def __call__(self, msg):
        d = dict(self.kwds)
        d.update(**{f:getattr(msg,f) for f in msg._fields})
        d.setdefault('now', self.env.now)
        print(self.template.format(**d))
        return msg

        
        
class collate(object):
    Dat = namedtuple('Collate','sequence_key number_per number_dst pattern_dst')
    def __init__(self, **kwds):
        self.dat = self.Dat(**{k:kwds[k] for k in self.Dat._fields})
    def __call__(self, msg):
        seqno = int(getattr(msg, self.dat.sequence_key))
        ind = seqno/int(self.dat.number_per)%int(self.dat.number_dst)
        dst = self.dat.pattern_dst%ind
        return msg._replace(dst=dst)
        
class sequence(object):
    def __init__(self, sequence_key = None, destinations=None, runlength=None,
                 **kwds):
        if not sequence_key or not destinations or not runlength:
            raise ValueError("Sequencer needs sequence_key and destinations")
        self.sequence_key = sequence_key
        self.destinations = destinations
        self.runlength = runlength
    def __call__(self, msg):
        seqno = int(getattr(msg, self.sequence_key))
        ind = seqno//int(self.runlength)%len(self.destinations)
        dst = self.destinations[ind]
        msg = msg._replace(src=msg.dst, dst=dst)
        print ('seqno=%d, ind=%d, rl=%d, dests=%s' % (seqno, ind, self.runlength, self.destinations))
        print ('collate: %s' % str(msg))
        return msg
