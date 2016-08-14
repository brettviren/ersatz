#!/usr/bin/env python
'''
Node services.
'''

from ersatz.units import Gbps, B, MB
from collections import defaultdict


class tx(object):
    '''
    A service which transmits incoming packets as smaller outgoing
    fragment packets.

    Outgoing fragment packets have three numbers added and one number
    changed:

        - `fragment_sequence` :: a number identify the original packet.

        - `fragment_index` :: sequentially number the outgoing
          fragment packet.

        - `fragment_count` :: total number of outgoing fragment
          packets.

        - `size` :: the size of the outgoing fragment packet.
    '''

    def __init__(self, **kwds):
        self.sequence_count = 0
        
    def __call__(self, env, packet, outs, fragment_size=8192*B, **kwds):

        seq = self.sequence_count
        self.sequence_count += 1

        size = packet['size']
        nfull = int(size // fragment_size)
        sizes = [fragment_size]*nfull
        last = int(size % fragment_size)
        if last:
            sizes.append(last)
            nfull += 1

        for count, psize in enumerate(sizes):
            outp = dict(packet, size=psize,
                        fragment_sequence=seq, fragment_index=count, fragment_count=nfull)
            for out in outs.values():
                yield out.put(outp)

class rx(object):
    '''
    A service that reassembles tx'ed fragment packets once all fragments have been found.

    Once all fragments are reassembled the resulting packet is put to all outs with no delay.

    It is as assumed there is no fragment packet loss nor duplication.
    '''
    def __init__(self, **kwds):
        self.sequences = defaultdict(list)

    def __call__(self, env, packet, outs, **kwds):
        seqno = packet['fragment_sequence']
        fragments = self.sequences[seqno]
        fragments.append(packet)
        nfragments = len(fragments)
        if nfragments != packet['fragment_count']:
            yield env.timeout(0.0)
            return
        self.sequences.pop(seqno)

        size = sum([f['size'] for f in fragments])

        rep = dict(fragments[0])
        rep.pop('fragment_sequence')
        rep.pop('fragment_index')
        rep.pop('fragment_count')
        rep['size'] = size
        for out in outs.values():
            yield out.put(rep)


def link(env, packet, outs, bandwidth=1*Gbps, latency=0, **kwds):
    '''
    A link which subjects the packet to a bandwidth delay and fixed
    latency.  It relies on the packet having a `size` attribute.
    After the delay, the packet is forwarded to all outs.
    '''
    delay = latency + packet['size'] / bandwidth
    yield env.timeout(delay)
    for out in outs.values():
        yield out.put(packet)
        

def switch(env, packet, outs, bandwidth=10*Gbps, latency=0, **kwds):
    '''
    Route the packet to the out with a name matching the `dst` value
    of the packet.  Bandwidth is the internal fabric bandwidth.
    '''
    dst = packet['dst']
    out = outs[dst]
    delay = packet['size']/bandwidth + latency
    yield env.timeout(delay)
    yield out.put(packet)
    
