#!/usr/bin/env python3

import simpy

from ersatz.units import GB, Gbps, B

from collections import namedtuple

Packet = namedtuple("Packet","src dst size payload")

DataSource = namedtuple("DataSource", "data ident size")
PortBuffer = namedtuple("PortBuffer", "data lock bandwidth frame_size")


def send_packet(env, pkt, port):
    with port.lock.request() as req:
        yield req           # only one write to port at a time
        yield env.timeout(pkt.size/port.bandwidth) # bandwidth latency
        yield port.data.put(pkt) # add packet to port queue
        print ("%.1f send: %s" % (env.now, str(pkt)))
        
def fabric(env, src, dsts):
    while True:
        pkt = yield src.data.get()
        dst = dsts[pkt.dst]
        yield dst.data.put(pkt)

def recv_packet(env, port, callback):
    while True:
        with port.lock.request() as req:
            yield req
            pkt = yield port.data.get() 
            yield env.timeout(pkt.size/port.bandwidth)
            callback(pkt)
        
def sendsomepackets(env, number, port, dsts, wait=1):
    for count in range(number):
        for dst in dsts:
            pkt = Packet("src",dst,8192*B,count)
            yield env.process(send_packet(env, pkt, port))
        yield env.timeout(wait)
    print ("%.1f sending done" % env.now)


def send_data(env, ident, data, port, src, dst, frame_size=8192*B):
    count = 0
    while True:
        amount = min(frame_size, data.level)
        if amount == 0.0:
            break
        yield data.get(amount)
        pkt = Packet(src,dst,amount, payload=dict(ident=ident, count=count))
        count += 1
        yield env.process(send_packet(env, pkt, port))
        

def sendsomefiles(env, number, port, src, dsts, wait=1):
    file_size = 200000*B
    for count in range(number):
        for dst in dsts:
            file = simpy.Container(env, capacity=file_size, init=file_size)
            yield env.process(send_data(env, "file_%s_%d" % (src, count), file, port, src, dst))

        yield env.timeout(wait)
    print ("%.1f sending done" % env.now)

class Printpkt(object):
    def __init__(self, env, ident):
        self.env = env
        self.ident=ident
    def __call__(self, pkt):
        print ("%.1f %s %s" % (self.env.now, self.ident, pkt))
        if self.ident != pkt.dst:
            print ("\tnot my packet")

def getsome(env, ports):
    
    for ident, port in ports.items():
        env.process(recv_packet(env, port, Printpkt(env, ident)))
        

def test_send_recv():

    env = simpy.Environment()

    enet_frame = 8192*B
    enet_bw = 1*Gbps

    srcport = PortBuffer(simpy.Store(env, capacity=1), simpy.Resource(env), enet_bw, enet_frame)
    oports = dict()
    for ind in range(5):
        oports["port%d"%ind] = PortBuffer(simpy.Store(env, capacity=1), simpy.Resource(env), enet_bw, enet_frame)
    
    env.process(sendsomefiles(env, 10, srcport, "src", oports.keys()))
    env.process(fabric(env, srcport, oports))
    getsome(env, oports)

    env.run(until=10000)



def port_buffer(env, srcs, dst, bandwidth, frame_size):
    count = 0
    while True:
        yield dst.get(frame_size)
        maybe = [s for s in srcs if s.level]
        ind = count%len(maybe)
        src = srcs[ind]
        amount = min(src.level, frame_size)
        yield src.get(amount)
        yield env.timeout(amount/bandwidth)
        
        
def buffered(env, ins, outs, linkbw, fabricbw, memory, frame_size):
    while True:
        if ins.level == 0:
            print ("idle")
            yield env.timeout(1) # idle....
            continue

        amount = min(ins.level, frame_size)
        yield memory.get(amount)
        yield ins.get(amount)

        yield env.timeout(amount / linkbw)
        #yield env.timeout(amount / fabricbw)
        yield outs.put(amount)
        yield memory.put(amount)
        

def monitor(env, name, st, target, to=1):
    yield env.timeout(0)
    initial_level = st.level
    t0 = env.now
    print ("%.1f %s: start at %s" % (env.now, name, t0))

    while True:
        yield env.timeout(to)

        print ("%.1f %s: %f GB" % (env.now, name, st.level/GB))

        if st.level == 0 or st.level == target:
            dt = env.now - t0
            bw = abs(initial_level-st.level)/dt
            print("%s: in %f sec: %f Gbps" % (name, dt, bw/Gbps))
            return



def test_one_link():

    env = simpy.Environment()

    data_size = 1*GB

    instream = simpy.Container(env, init=data_size, capacity=data_size)
    outstream = simpy.Container(env, capacity=data_size)
    env.process(monitor(env, 'tx', instream, data_size))
    env.process(monitor(env, 'rx', outstream, data_size))

    memory = simpy.Container(env, init=8192*B, capacity=8192*B)
    env.process(buffered(env, instream, outstream, 1*Gbps, 10*Gbps, memory, 8192*B))
    env.run(until=10)

if '__main__' == __name__:
#    test_one_link()
    test_send_recv()
