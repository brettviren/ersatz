#!/usr/bin/env python3

import simpy

from ersatz.util import get_method

def queue(env, name, kind, **kwds):
    if kind.lower() in ["source"]:
        return None             # interpreted by ersatz.node.Node

    if kind is None or kind.lower() in ["default","queue"]:
        try:
            cap = kwds['queue_capacity']
        except KeyError:
            return simpy.Store(env)
        else:
            return simpy.Store(env, capacity = cap)

    meth = get_method(kind)     # assume it's a FQN
    return meth(**kwds)




def service(env, name, kind, **kwds):
    meth = get_method(kind)     # assume it's a FQN
    if type(meth) == type:      # if class, instantiate
        meth = meth(**kwds)
    return meth

defaults = dict(queue=queue, service=service)

