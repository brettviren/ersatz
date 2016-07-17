#!/usr/bin/env python

from collections import defaultdict, namedtuple
import simpy
from ersatz.units import MB, second
from ersatz.node import Node
from ersatz.datum import Datum

def parse_address(addr):
    name,number = addr.rsplit('.',1)
    return name,int(number)
def make_address(name,num):
    return "%s.%d" % (name,num)

class BoardReader(object):
    def __init__(self, router):
        self.router = router
    def __call__(self, datum):
        ouraddr = datum.rxaddr
        nam,num = parse_address(ouraddr)
        pl = datum.payload
        ebaddr = self.router(pl)
        da = Datum(ouraddr, ebaddr, datum.size, pl)
        yield 0,da

Event = namedtuple("Event", "trigger fragments")

class EventBuilder(object):
    def __init__(self, nfragments, router):
        self.nfragments = nfragments
        self.router = router
        self.events = defaultdict(list)
        self.delay = 0.25*second # fixme, do something more interesting


    def __call__(self, datum):
        ouraddr = datum.rxaddr
        nam,num = parse_address(ouraddr)

        pl = datum.payload
        self.events[pl.trigger].append(datum)

        ready = {t:l for t,l in self.events.items() if l.size() == self.nfragments}
        ret = list()
        for t,l in ready.items():
            self.events.pop(t)
            size = sum([d.size for d in l])
            payload = Event(fragments = [d.payload for d in l],
                            trigger = l[0].trigger)
            addr = self.router(payload)
            yield self.delay, Datum(ouraddr, addr, size, payload)
        

def test_daq():
    env = simpy.Environment()

    fragment_size = 2.5*MB
    trigger_period = 25*second
    nboardreaders = 100
    neventbuilders = 20
    neventsperfile = 50

    def br_router(pl):
        ebnum = pl.trigger // neventsperfile % neventbuilders
        return make_address("eb",ebnum)

    def eb_router(pl):
        return "sink"

    layer_boardreaders = list()
    for count in range(nboardreaders):
        node = Node(env, BoardReader(br_router))
        layer_boardreaders.append(node)

    layer_eventbuilders = list()
    for count in range(neventbuilders):
        node = Node(env, EventBuilder(nboardreaders, eb_router))
        layer_eventbuilders.append(node)

if '__main__' == __name__:
    test_daq()
    
