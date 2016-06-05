from StringIO import StringIO
from ersatz.config import Configuration
from ersatz.app import ObjectStore

from fodder import cfgstr

def test_object_store():
    s = StringIO(cfgstr)
    c = Configuration(s)
    objects = ObjectStore("env", c)
    for thing in 'network router layer host process function'.split():
        cat = getattr(c,thing)
        assert(cat)
        print thing
        for name in cat:
            print '\t%s' % name

            o = objects.get(thing, name)
            assert(o)
            print '\t%s' % o


if '__main__' == __name__:
    test_object_store()
