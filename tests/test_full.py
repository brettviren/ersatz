#!/usr/bin/env pypthon

import simpy
from ersatz.net import Host, router, Pipeline, Generator, Message, Sink
from ersatz.units import MB, ms, Gbps, second
from ersatz.functions import sequence, dumpmsg

class function_collate(object):
    def __init__(self, key, count, dstpat, **kwds):
        self.key = key
        self.count = count
        self.dstpat = dstpat
    def __call__(self, msg):
        number = getattr(msg, self.key)
        dst = self.dstpat % number
        return msg._replace(dst=dst)
    

def nameit(prefix,number):
    return "%s%d"%(prefix, number)

class DetectorFragment(object):
    def __init__(self, env, src, dst, size, delay = second):
        self.env = env
        self.src = src
        self.dst = dst
        self.size = size
        self.delay = delay
        self.count = 0;

    def prepare(self):
        return self.env.timeout(self.delay)

    def __call__(self):
        msg = Message(self.src, self.dst, self.size,
                      fragment = self.src,
                      seqnum = self.count, dftime = self.env.now)
        print ('DF: %s' % str(msg))
        self.count += 1
        return msg
                       

def test_full():

    env = simpy.Environment()

    num_detector_fragments=4
    num_event_builders=2
    fragsize = 10*MB

    print ('Detector Fragments')
    dfs = list()
    for count in range(num_detector_fragments):
        src = nameit("df", count)
        dst = nameit("br", count) # one-to-one
        func = DetectorFragment(env, src, dst, fragsize)
        df = Host(env, src, Generator(func))
        dfs.append(df)

    print ('Board Readers')
    brs = list()
    eb_names = [nameit("eb", num) for num in range(num_event_builders)]
    print (str(eb_names))
    for count in range(num_detector_fragments):
        src = nameit("br", count)
        func = sequence('seqnum', eb_names, 10)
        br = Host(env, src, Pipeline([func]))
        brs.append(br)
        
    print ('Event Builders')
    ebs = list()
    for count in range(num_event_builders):
        src = nameit("eb", count)
        func = dumpmsg(env, "Building event #{seqnum} {now} {src} --> {dst} {size}")
        eb = Host(env, src, Sink(func))
        ebs.append(eb)

    router(env, dfs, brs, delay=100*ms, bandwidth=Gbps)
    router(env, brs, ebs, delay=100*ms, bandwidth=Gbps)

    SIM_DURATION = 100
    env.run(until=SIM_DURATION)

if '__main__' == __name__:
    test_full()
    


