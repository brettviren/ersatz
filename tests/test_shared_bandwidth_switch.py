#!/usr/bin/env python3

from collections import namedtuple, defaultdict

StreamAddress = namedtuple('StreamAddress','inport outport')

class Stream(object):
    def __init__(self, addr):
        self.addr = addr
        self.bandwidth = 0


class Switch(object):
    def __init__(self, bandwidth):
        self.bandwidth = bandwidth
        self.instream = defaultdict(set)
        self.outstream = defaultdict(set)

    def stage(self, stream):
        inport = self.instream[stream.addr.inport]
        inport.add(stream)
        outport = self.outstream[stream.addr.outport]
        outport.add(stream)
        # prime stream bandwidth
        stream.bandwidth = 2*self.bandwidth / (len(inport)+len(outport))

    def unstage(self, stream):
        try:
            self.instream[stream.addr.inport].pop(stream)
        except KeyError:
            pass
        try:
            self.outstream[stream.addr.outport].pop(stream)
        except KeyError:
            pass

    def balance_one(self, ports):
        maxadj = 0
        for port, streams in ports.items():
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



    def imbalance(self):

        def do_one(what, ports):
            for port,streams in ports.items():
                bw = sum([s.bandwidth for s in streams])
                per = 100*bw/self.bandwidth
                print ('%s%d: %.1f/%.0f = %.2f%%' % (what, port, bw, self.bandwidth, per))
        do_one('in', self.instream)
        do_one('out', self.outstream)


    def dot(self):
        ret = ['digraph switch {','rankdir=LR;']
        for port,streams in self.instream.items():
            for s in streams:
                ret.append('in%d -> out%d[label="%.1f"];' % (s.addr.inport,s.addr.outport,s.bandwidth))
        ret.append('}')
        return '\n'.join(ret)
        
        

def test_balance():
    sw = Switch(100)
    for ip in range(5):
        for op in range(max(0,ip-2),min(5,ip+2)):
            sw.stage(Stream(StreamAddress(ip,op)))
    
    imb,count = sw.balance()
    print ('%d iters: max adj: %.1f' % (count, imb))
    sw.imbalance()

    with open('test_balance.dot','w') as fp:
        fp.write(sw.dot())
    

if '__main__' == __name__:
    test_balance()
    
