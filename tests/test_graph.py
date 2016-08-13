#!/usr/bin/env python3

import networkx as nx
import ersatz.graph
import simpy

def generator(env, packet, outs, delay=1, **kwds):
    count = 0
    while True:
        print ("generate: %d for %d" % (count, len(outs)))
        for out in outs.values():
            yield out.put(count)
        yield env.timeout(delay)
        count += 1

def delay(env, packet, outs, timeout=1, **kwds):
    yield env.timeout(timeout)
    for out in outs.values():
        yield out.put(packet)

def sink(env, packet, outs, **kwds):
    print ("sink: %s" % packet)
    yield env.timeout(0.0)

def test_graph():
    g = nx.DiGraph()
    g.add_node("source", service=generator, capacity=0)
    g.add_node("delay", service=delay)
    g.add_node("sink", service=sink)

    g.add_edge("source","delay")
    g.add_edge("delay","sink")
    env = simpy.Environment()
    nodes = ersatz.graph.objectify(env, g)
    for name,node in nodes.items():
        print (name,node.queue,node.outs)

    env.run(until=20)


if '__main__' == __name__:
    test_graph()
    
