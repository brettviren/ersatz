#!/usr/bin/env python3
'''
Provides a model for a shared bandwidth switch.
'''

import simpy
from collections import namedtuple, defaultdict

class Stream(object):
    def __init__(self, inport, outport, size, now=None, payload=None):
        '''
        Bookkeeping for each stream managed by a Switch.
        '''
        self.inport = inport
        self.outport = outport
        self.size = size
        self.start = now
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
        Return time to complete stream at current bandwidth.
        '''
        return self.remaining / self.bandwidth

    def __lt__(self, other):
        if self.remaining < other.remaining: return True
        if self.size < other.size: return True
        if self.start < other.start: return True
        return id(self) < id(other)

    def __str__(self):
        return 'stream %s --> %s start at %d, remaining: %.1f/%.1f (%.2f%%) bw=%.1f' % \
            (self.inport, self.outport, self.start, self.remaining, self.size,
             100.0*self.remaining/self.size, self.bandwidth)

class Switch(object):
    '''
    A shared bandwidth switch.
    '''
    def __init__(self, env, bandwidth):
        '''
        Create a shared bandwidth switch with each port having the given bandwidth.
        '''
        self.env = env
        self.bandwidth = bandwidth

        self.instream = defaultdict(set)
        self.outstream = defaultdict(set)

        if env:
            self.inbox = simpy.Store(env) # streams start
            self.outbox = simpy.Store(env) # streams finish
            self.transmit = simpy.PreemptiveResource(env, capacity=1)
            env.process(self.accept())

    @property
    def streams(self):
        '''
        Return set of all streams
        '''
        streamlists = [s for s in self.instream.values()] + [s for s in self.outstream.values()]
        return {s for sl in streamlists for s in sl}

    def accept(self):
        '''
        Poll inbox and deliver new streams as they are provided.
        '''
        while True:
            stream = yield self.inbox.get()
            print ('accept with %d ongoing:  %s' % (len(self.streams), stream))
            self.env.process(self.deliver(stream))

    def stage(self, stream):
        '''
        Add a new stream to the switch.
        '''
        inport = self.instream[stream.inport]
        inport.add(stream)
        outport = self.outstream[stream.outport]
        outport.add(stream)
        # prime stream bandwidth
        stream.bandwidth = 2*self.bandwidth / (len(inport)+len(outport))


    def unstage(self, stream):
        '''
        Remove stream from switch.
        '''
        try:
            self.instream[stream.inport].discard(stream)
        except KeyError:
            pass
        try:
            self.outstream[stream.outport].discard(stream)
        except KeyError:
            pass

    def balance_one(self, port_streams):
        '''
        Make one pass at balancing bandwidths for given port-stream associations.
        '''
        maxadj = 0
        for port, streams in port_streams.items():
            if len(streams) <= 1:
                continue
            totbw = sum([s.bandwidth for s in streams])
            relbw = (totbw - self.bandwidth)/totbw
            #print ('%6.2f'%relbw) 
            for s in streams:
                adj = relbw*s.bandwidth
                s.bandwidth -= adj
                maxadj = max(maxadj, adj)
        return maxadj

    def balance(self, precision=0.01, maxiter=10):
        '''
        Balance the bandwidths of the individual streams until reaching relative precision or maxiter.
        '''
        def do_pair():
            madj1 = self.balance_one(self.instream)
            madj2 = self.balance_one(self.outstream)
            return max(madj1, madj2)
        lastimb = None
        for count in range(maxiter):
            imb = do_pair()
            if not lastimb is None and abs(imb - lastimb) < self.bandwidth*precision:
                return (imb,count)
            lastimb = imb
        return (lastimb, maxiter)



    def dump(self):
        '''
        Dump information about the switch
        '''

        def do_one(what, ports):
            for port,streams in ports.items():
                bw = sum([s.bandwidth for s in streams])
                per = 100*bw/self.bandwidth
                print ('%s%d: %.1f/%.0f = %.2f%%' % (what, port, bw, self.bandwidth, per))
        do_one('in', self.instream)
        do_one('out', self.outstream)


    def dot(self):
        '''
        Return state of switch as a GraphViz dot string.
        '''
        ret = ['digraph switch {','rankdir=LR;']
        for port,streams in self.instream.items():
            for s in streams:
                ret.append('in%d -> out%d[label="%.1f"];' % (s.inport,s.outport,s.bandwidth))
        ret.append('}')
        return '\n'.join(ret)
        

    def find_next(self):
        '''
        Return stream with smallest ETA
        '''
        streams = self.streams
        if not streams:
            return None
        etas = [(s.eta,s) for s in streams]
        etas.sort()
        print ('\n'.join(["%.1f: %s" % (t,s) for t,s in etas]))
        return etas[0][1]

    def update(self, elapsed):
        '''
        Update each stream after time elapsed since last update.
        '''
        for s in self.streams:
            s.update(elapsed)
            print ('\tupdated: %s' % str(s))
        return

    def deliver(self, stream):
        '''
        Deliver new stream.

        This preempts any delivery already in progress.
        '''
        prio = -1*len(self.streams)
        print ('GRAB with priority %d' % prio)
        with self.transmit.request(priority=prio) as req: # this prempts any existing delivery
            yield req
            self.stage(stream)
            self.balance()
            stream = self.find_next()
            start = self.env.now
            print ('delivering t=%.1f prio=%d: %s' % (start, prio, stream))
            try:
                yield self.env.timeout(stream.eta)
            except simpy.Interrupt: # someone else came to deliver
                print ('INTERUPTED %s' % str(stream))
                self.update(self.env.now-start)
                return

            # reach here, successfully waited out a stream to finish
            elapsed = self.env.now - start
            self.update(elapsed)
            print ('delivered after %.1f: %s' % (elapsed, stream))
            self.unstage(stream)
            yield self.outbox.put(stream)

        stream = self.find_next()
        print ('moving on to: %s' % stream)
        if stream:
            self.env.process(self.deliver(stream))

        
