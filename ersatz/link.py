class Link(object):
    '''
    Model a single shared bandwidth link.
    '''
    def __init__(self, env, switch):
        self.env = env
        self.streams = dict()
        self.bandwidth = bandwidth
        self.inbox = simpy.Store(env) # streams start
        self.outbox = simpy.Store(env) # streams finish
        self.transmit = simpy.PreemptiveResource(env, capacity=1)
        env.process(self.accept())


    def accept(self):
        while True:
            stream = yield self.inbox.get()
            print ('accept with %d ongoing:  %s' % (len(self.streams), stream))
            self.env.process(self.deliver(stream))

    def stage(self, stream):
        "Stage a stream"
        self.streams[stream.ident] = stream
        nstreams = len(self.streams)
        bw = self.bandwidth / nstreams
        for s in self.streams.values():
            s.bandwidth = bw
        print ('staged with bw=%.1f and %d streams: %s' % (bw, nstreams, stream))

    def unstage(self, stream):
        self.streams.pop(stream.ident)
        nstreams = len(self.streams)
        print ('unstaged with %d streams: %s' % (nstreams, stream))
        if not nstreams:
            return
        bw = self.bandwidth / nstreams
        for s in self.streams.values():
            s.bandwidth = bw

    def find_next(self):
        "Return stream with smallest ETA"
        if not self.streams:
            return None
        etas = [(s.eta,s) for s in self.streams.values()]
        etas.sort()
        print ('\n'.join(["%.1f: %s" % (t,s) for t,s in etas]))
        return etas[0][1]

    def update(self, elapsed):
        "Update all streams after elapsed"
        for s in self.streams.values():
            s.update(elapsed)
            print ('\tupdated: %s' % str(s))
        return

    def deliver(self, stream):
        prio = -1*len(self.streams)
        print ('GRAB with priority %d' % prio)
        with self.transmit.request(priority=prio) as req: # this prempts any existing delivery
            yield req
            self.stage(stream)
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
