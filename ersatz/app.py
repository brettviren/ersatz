from collections import OrderedDict

class ObjectStore(object):

    def __init__(self, env, cfg):
        self.env = env
        self.cfg = cfg
        for cat in cfg.factories:
            setattr(self, cat, OrderedDict())

    def get(self, cat, name):
        objs = getattr(self, cat)
        try:
            return objs[name]
        except KeyError:
            pass

        catcfg = getattr(self.cfg, cat)
        ocfg = catcfg[name]
        obj = ocfg.factory(self.env, name, ocfg)
        objs[name] = obj
        return obj

class Application(object):
    def __init__(self, env, cfg):
        self.env = env
        self.cfg = cfg
        self.obj = ObjectStore(env, cfg)

        
