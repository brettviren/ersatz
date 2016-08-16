from importlib import import_module

import re
import ersatz.units as units

def units_dict():
    return {k:v for k,v in units.__dict__.items() if not k.startswith('_')}

def listify(string):
    return re.split('[, \t\n]+', string)


def bytes_str(B):
    if B < 1e3:
        return "%d B" % (B/units.Byte,)
    if B < 1e6:
        return "%.1f kB" % (B/units.kB,)
    if B < 1e9:
        return "%.1f MB" % (B/units.MB,)
    return "%.1f GB" % (B/units.GB)

def is_string(thing):
    if isinstance(thing, type(u"")):
        return True
    if isinstance(thing, type("")):
        return True
    return False

def unitify(thing, **kwds):
    if not is_string(thing):
        return thing
    return eval(thing, units_dict(), kwds)

def get_method(dotpath):
    if not isinstance(dotpath, type("")):
        return dotpath
    try:
        modname, methname = dotpath.rsplit('.',1)
    except ValueError:
        print ('dotpath = "%s"' % dotpath)
        raise
    mod = import_module(modname)
    return getattr(mod, methname)

