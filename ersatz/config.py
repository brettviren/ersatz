#!/usr/bin/env python
import os
from collections import OrderedDict

import ersatz.factories
from ersatz.util import get_method


class Configuration(object):
    """The purpose of the Configuration object is to turn the textual
    configuration information into objects.
    """

    def __init__(self, file=None):
        from ConfigParser import RawConfigParser as configparser
        cfg = configparser()

        if hasattr(file, 'readline'): # file like object
            cfg.readfp(file)
        else:
            filename = os.path.expanduser(os.path.expandvars(file))
            cfg.read(filename)

        for secname in cfg.sections():
            kwds = {i[0]:i[1] for i in cfg.items(secname)}
            cat, name = secname.split()

            objstore = self.__dict__.setdefault(cat, OrderedDict())

            try:
                factory = kwds.pop('factory')
            except KeyError:
                factory = getattr(ersatz.factories, cat)
            else:
                factory = get_method(factory)

            objstore[name] = factory(name, **kwds)
