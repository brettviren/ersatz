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
import importlib
import ersatz.node
import ersatz.factory
from ersatz.util import get_method


def objectify(g, env, factories = ersatz.factory.defaults):
    '''
    Convert in place some graph node attributes to objects.

    If a node attribute key is in the factories dictionary, run the
    corresponding factory to produce the object and replace the
    attribute value with the object.

    Graph attributes provide defaults for all node attributes.  Node
    attributes are passed to factory.::

        factory(env, key, value, **node_attr) -> object
    '''
    defaults = dict(g.graph)
    for node in g.nodes():
        attrs = dict(defaults)
        attrs.update(g.node[node])
        objs = dict()
        for key, value in attrs.items():
            try:
                fac = factories[key]
            except KeyError:
                continue
            obj = fac(env, key, value, **attrs)
            #print ("objectify: %s %s %s -> %s" % (node, key, value, obj))
            objs[key] = obj
        g.node[node].update(objs)

    return g


def nodify(g, env):
    '''
    Return dict keyed by node name of ersatz.node.Node objects
    configured and connected via given graph using the objects at node
    attributes `queue` and `service`.
    '''
    queues = dict()
    for node in g.nodes():
        #print (node, g.node[node])
        queues[node] = g.node[node]["queue"]

    ret = dict()
    defaults = dict(g.graph)
    for node in g.nodes():
        attrs = dict(defaults)
        attrs.update(g.node[node])

        service = attrs.pop('service')
        queue = attrs.pop('queue')
        #print ("Nodify: %s %s %s" % (node,service,queue))

        outs = {n:queues[n] for n in g.edges[node]}
        ret[node] = ersatz.node.Node(env, queue, service, outs, **attrs)

    return ret

def _objectify(env, spec):
    '''

    Interpret the "spec" graph into ersatz.node.Node objects.

    Nodes in the spec graph are identified by a name.

    Node attributes may contain keyword options.  Some are reserved,
    interpreted and removed.  Any remaining are passed to the service.

        - `queue` :: a Python dotted path to a factory method taking a
          simpy Environment object and which produces an instance of a
          queue object.  Default produces a simpy.Store with infinite
          capacity.  See ersatz.queue for what batteries are included.

        - `service` :: a Python dotted path to a generator as a class
          or function which provides the service functionality.

    Graph attributes serve as default for node attributes.
    '''
    args = dict()
    defaults = dict(spec.graph)
    for node in spec.nodes():
        attrs = dict(defaults)
        attrs.update(spec.node[node])

        queuename = attrs.pop("queue", "ersatz.queue.default")
        servicename = attrs.pop('service')

        queuefactory = get_method(queuename)
        queue = queuefactory(env, **attrs)

        service = get_method(servicename)
        if type(service) == type: # a class
            service = service(**attrs)

        args[node] = (queue, service, attrs)

    ret = dict()
    for node in spec.nodes():
        q, s, k = args[node]
        outs = {n:args[n][0] for n in spec.edge[node]}
        ret[node] = ersatz.node.Node(env, q, s, outs, **k)
            
    return ret
