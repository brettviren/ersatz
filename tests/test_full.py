#!/usr/bin/env pypthon

def function_dumpmsg(msg):
    print msg
    return 

class function_collate(object):
    def __init__(self, key, count, dstpat, **kwds):
        self.key = key
        self.count = count
        self.dstpat = dstpat
    def __call__(self, msg):
        number = getattr(msg, self.key)
        dst = self.dstpat % number
        return msg._replace(dst=dst)
    

def test_full():
    pass


