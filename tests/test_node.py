#!/usr/bin/env python3
'''
Test ersatz.node
'''

import simpy
from ersatz.node import Node

def test_simple():

    env = simpy.Environment()
    def service_delay(packet, outs):
        print ("%f delay, packet: %s" % (env.now, packet))
        yield env.timeout(1)
        yield outs[0].put(packet)
        print ("%f delay done, packet: %s" % (env.now,packet))

    def generate(source):
        for count in range(10):
            print ("generate packet: %d" % count)
            yield source.put(count)
            yield env.timeout(.1)

    source = simpy.Store(env)
    env.process(generate(source))
    sink = simpy.Store(env)
    n1 = Node(env, source, service_delay, outs=[sink])

    env.run(until=100)
    print (len(sink.items))

if '__main__' == __name__:
    test_simple()
    
