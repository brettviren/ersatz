#!/usr/bin/env python3

import networkx as nx
import ersatz.graph
from ersatz.units import Gbps, ms, MB
import simpy
import matplotlib.pyplot as plt

def generator(env, packet, outs, number=10, ndsts=2, delay=1, size=1*MB, **kwds):

    for count in range(number):
        idst = (count%ndsts) + 1
        dst = "rxlink%d" % idst
        print ("%.2f generate: %d for %s" % (env.now, count, dst))
        for out in outs.values():
            yield out.put(dict(size=size, count=count, dst=dst))
        yield env.timeout(delay)


def sink(env, packet, outs, delay=1000*ms, **kwds):
    yield env.timeout(delay)
    print ("%.2f sink: %d %s (delay=%.1f)" % (env.now, packet['count'], packet['dst'], delay))


def test_graph():
    g = nx.DiGraph()

    bandwidth = 1*Gbps

    g.add_node("source", service=generator, number=10, queue="source", size=100*MB)
    g.add_node("tx", service='ersatz.service.tx', fragment_size=10*MB)
    g.add_node("txlink", service='ersatz.service.link', bandwidth=bandwidth)
    g.add_node("switch", service='ersatz.service.switch')
    g.add_node("rxlink1", service='ersatz.service.link', bandwidth=bandwidth)
    g.add_node("rxlink2", service='ersatz.service.link', bandwidth=bandwidth)
    g.add_node("rx1", service='ersatz.service.rx')
    g.add_node("rx2", service='ersatz.service.rx')
    g.add_node("sink1", service=sink, delay=1000*ms)
    g.add_node("sink2", service=sink, delay=10000*ms)


    g.add_edge("source", "tx")
    g.add_edge("tx", "txlink")
    g.add_edge("txlink", "switch")
    g.add_edge("switch", "rxlink1")
    g.add_edge("switch", "rxlink2")
    g.add_edge("rxlink1","rx1")
    g.add_edge("rxlink2","rx2")
    g.add_edge("rx1","sink1")
    g.add_edge("rx2","sink2")

    
    g.graph["queue"] = "default"

    nx.drawing.nx_agraph.write_dot(g, "test_graph.dot")

    env = simpy.Environment()
    #nodes = ersatz.graph.objectify(env, g)
    ersatz.graph.objectify(g, env)
    nodes = ersatz.graph.nodify(g, env)

    env.run(until=200)


if '__main__' == __name__:
    test_graph()
    
