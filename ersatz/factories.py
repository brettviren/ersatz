from ersatz.util import listify, unitify
import ersatz.net

class network(object):
    """
    A network is responsible for finding its routers and running them.
    """

    def __init__(self, name, routers=None, **kwds):
        self.name = name
        if not routers:
            raise ValueError, "a network needs at least one router"
        self.routers = routers

    def __call__(self, env, objstore):
        for rname in self.routers:
            router = objstore.router[rname]
            router(env, objstore)

class router(object):
    """A router is responsible transmitting packets between its hosts by
    starting a SimPy process to receive from each host and send based
    on the destination.
    """

    def __init__(self, name, layers = None, bandwidth = None, delay = None, **kwds):
        if not layers:
            raise ValueError, "a router needs at least one layer"
        self.name = name
        self.layers = listify(layers)
        self.bandwidth = unitify(bandwidth)
        self.delay = unitify(bandwidth)

    def __call__(self, env, objstore):
        all_hosts = list()
        for lname in self.layers:
            layer = objstore.layer[lname]
            for hostname in layer.hostnames:
                host = objstore.host[hostname]
                all_hosts.append(host)
        erstatz.net.router(env, all_hosts, self.delay, self.bandwidth)
    
class layer(object):
    """A layer is a group of hosts which run the same processes."""
    def __init__(self, name, nhosts=0, hostname="", pipeline="",**kwds):
        if not nhosts or not protohost or not pipeline:
            raise ValueError, "a layer needs some hosts and a pipeline"
        self.hostnames = [hostname%d for d in range(nhosts)]
        self.pipeline = listify(pipeline)

    def __call__(self, env, objstore):
        pass




import ersatz.functions
def function(name, **kwds):
    factory = getattr(ersatz.functions, name)
    return factory(**kwds)



