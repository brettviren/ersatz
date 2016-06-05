from StringIO import StringIO
from ersatz.config import Configuration

from fodder import cfgstr

def test_config():
    s = StringIO(cfgstr)
    
    c = Configuration(s)
    for thing in 'network router layer host process function'.split():
        cat = getattr(c,thing)
        assert(cat)
        print thing, cat
        for name, obj in cat.items():
            print '\t%s: %s' % (name,obj)
            for aname, aobj in obj.__dict__.items():
                if aname.startswith('_'):
                    continue
                print '\t\t%s: %s' % (aname, aobj)

if '__main__' == __name__:
    test_config()
