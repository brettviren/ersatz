#!/usr/bin/env python
'''
An ersatz graph defines the connectivity of erstatz Nodes.

There are various types of ersatz graphs.

spec graph

A graph composed of parameters. 

spec node

Node should be a unique name.
Reserved node attributes include

- `capacity` :: give the capacity of the queue (default or negative gives an infinite queue)
- `service` :: a Python dot.path to a callable.
- `nservices` :: number of concurrent instances of the service
 
All other node attributes passed to the service as keyword arguments on instantiation.

'''

import simpy
import networkx as nx
import importlib
import ersatz.node

def objectify(env, spec):
    '''
    Interpret a spect graph into an object graph.


    Nodes in the spec graph are identified by a name.  The node
    attribute "service" should be a Python dot.path to a service
    callable.  Any remaining attributes will be passed to the service.
    '''
    args = dict()
    for node in spec.nodes():
        attrs = spec.node[node]
        capacity = attrs.pop("capacity", float("inf"))
        queue = None
        if capacity > 0:
            queue = simpy.Store(env, capacity)
        service = attrs.pop('service')

        if isinstance(service, type("")):
            modname, methname = service.rsplit('.',1)
            mod = importlib.import_module(modname)
            service = getattr(mod, methname)
        args[node] = (queue, service, attrs)

    ret = dict()
    for node in spec.nodes():
        q, s, k = args[node]
        outs = {n:args[n][0] for n in spec.edge[node]}
        ret[node] = ersatz.node.Node(env, q, s, outs, **k)
            
    return ret
