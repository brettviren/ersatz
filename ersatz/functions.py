'''

Message processing functions.

'''
from collections import namedtuple

from ersatz.util import unitify
from ersatz.net import Message

class generate(object):
    def __init__(self, src='', dst='', size='', **kwds):
        if not size or not src or not dst:
            raise ValueError, 'generate needs a src, dst and size'
        self.dat = dict(size= unitify(size),
                        src = src,
                        dst = dst, **kwds)
    def __call__(self, msg):
        d = dict()
        d.update(**{f:getattr(msg,f) for f in msg._fields})
        d.update(**self.dat)
        return Message(**d)


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
    def __init__(self, template="", **kwds):
        self.template = template
        self.kwds = kwds
    def __call__(self, msg):
        d = dict(self.kwds)
        d.update(**{f:getattr(msg,f) for f in msg._fields})
        print self.template.format(**d)
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
        
