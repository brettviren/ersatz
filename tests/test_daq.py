#!/usr/bin/env python

from collections import defaultdict, namedtuple
import simpy
from ersatz.units import MB, second, Gbps, ms
from ersatz.node import Node
from ersatz.datum import Datum
from ersatz.switch import LinkedSwitch

def parse_address(addr):
    name,number = addr.rsplit('.',1)
    return name,int(number)
def make_address(name,num):
    return "%s.%04d" % (name,num)

class BoardReader(object):
    'A board reader node transform'
    def __init__(self, router, delay=1.0*ms):
        self.router = router
        self.delay = delay
    def __call__(self, datum):
        ouraddr = datum.rxaddr
        nam,num = parse_address(ouraddr)
        pl = datum.payload
        ebaddr = self.router(pl)
        da = Datum(ouraddr, ebaddr, datum.size, pl)
        #print ("BR send: %s" % da)
        return [(self.delay,da)]

Event = namedtuple("Event", "trigger fragments")


class EventBuilder(object):
    'An event builder node transform'
    def __init__(self, nfragments, router):
        self.nfragments = nfragments
        self.router = router
        self.events = defaultdict(list)
        self.delay = 0.25*second # fixme, do something more interesting


    def __call__(self, datum):
        ouraddr = datum.rxaddr
        nam,num = parse_address(ouraddr)

        #print ("EB recv: %s" % datum)

        pl = datum.payload
        self.events[pl.trigger].append(datum)

        #print ("EB #%03d @%05.2f %s -> %s (holding %d events)" %
        #       (pl.trigger, pl.trigtime, ouraddr, datum.txaddr, len(self.events)))
        #print ("\t%s" % (','.join("%d:%d" % (t,len(l)) for t,l in self.events.items())))


        ready = {t:l for t,l in self.events.items() if len(l) == self.nfragments}

        ret = list()
        for t,l in ready.items():
            self.events.pop(t)
            size = sum([d.size for d in l])
            payload = Event(fragments = [d.payload for d in l],
                            trigger = l[0].payload.trigger)
            addr = self.router(payload)
            #print ("EB %s: trig: #%d at %.02fs" % (ouraddr, t, l[0].payload.trigtime))
            dd = self.delay, Datum(ouraddr, addr, size, payload)
            ret.append(dd)

        return ret
        

class Fragment(object):
    def __init__(self, trigger, fragnum, trigtime):
        self.trigger = trigger
        self.fragnum = fragnum
        self.trigtime = trigtime
    def __str__(self):
        return "trig=%003d frag=%003d t=%.02f" % (self.trigger, self.fragnum, self.trigtime)

def fragment_source(env, trig, fragnum, size, brrx):
    '''
    Be both fragment generator and deliverer
    '''
    trignum = 0
    while True:
        yield env.timeout(trig())
        da = Datum(make_address('fr', fragnum), # hard code routing policy
                   make_address('br', fragnum), # of one-to-one fr-br
                   size,
                   Fragment(trignum, fragnum, env.now))
        if fragnum == 0:
            print ("trigger %d at %.1f" % (trignum, env.now))
        trignum += 1
        yield brrx.put(da)
        
def event_sink(env, rx):
    while True:
        da = yield rx.get()
        pl = da.payload

        print ("SINK: trig %d @%.1f from %s with %d fragments" % (pl.trigger, env.now, da.txaddr, len(pl.fragments)))
        
def test_daq():
    env = simpy.Environment()

    fragment_size = 2.5*MB
    #trigger_period = (1.0/25.0)*second
    trigger_period = 1.0*second
    nboardreaders = 100
    neventbuilders = 20
    neventsperfile = 50

    def constant_trigger():
        return trigger_period

    def br_router(pl):
        ## if we keep sequential triggers into the EBs:
        #ebnum = pl.trigger // neventsperfile % neventbuilders
        ## if we round robbin at the trigger level
        ebnum = pl.trigger % neventbuilders
        return make_address("eb",ebnum)

    def eb_router(pl):
        return "sink"

    lsw = LinkedSwitch(env, 1*Gbps)

    # every BR is in fact stateless, identical so just make one object
    BR = BoardReader(br_router)

    layer_boardreaders = list()
    for count in range(nboardreaders):
        node = Node(env, BR)
        layer_boardreaders.append(node)

        braddr = make_address("br", count)

        lsw.link_nic(braddr, node.rx, node.tx)

    layer_eventbuilders = list()
    for count in range(neventbuilders):
        node = Node(env, EventBuilder(nboardreaders, eb_router))
        layer_eventbuilders.append(node)

        ebaddr = make_address("eb", count)
        lsw.link_nic(ebaddr, node.rx, node.tx)


    for count, node in enumerate(layer_boardreaders):
        env.process(fragment_source(env, constant_trigger, count, fragment_size, node.rx))

    sinkrx = simpy.Store(env)
    lsw.link_nic("sink", sinkrx, None)
    env.process(event_sink(env, sinkrx))

    env.run(until=100)

if '__main__' == __name__:
    test_daq()
    
