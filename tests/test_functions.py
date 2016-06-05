from ersatz.net import Message
from ersatz.units import MB

from ersatz.functions import dumpmsg, collate, compress, roundrobin, generate

def test_generate():
    count = 42
    fun = generate(src="src", dst="dst", size=10*MB, extra='blah')
    msg = Message("foo","dsbar",1*MB,count=count)
    newmsg = fun(msg)
    #print newmsg
    assert (newmsg.src == "src")
    assert (newmsg.dst == "dst")
    assert (newmsg.size == 10*MB)
    assert (newmsg.extra)
    assert (newmsg.count == count)
    
def test_robin():
    ndst=3
    pdst='dst%02d'
    fun  = roundrobin(sequence_key='count', number_dst=ndst,
                      pattern_dst=pdst)
    counts=[0]*ndst
    for count in range(30):
        msg = Message("src","dst",10*MB,count=count)
        newmsg = fun(msg)
        want = count%ndst
        counts[want] += 1
        dst = pdst%want
        #print newmsg.dst, dst
        assert newmsg.dst == dst
    assert(counts[0] == counts[1])
    assert(counts[0] == counts[2])
    assert(counts[0] == 10)

def test_collate():
    nper=10
    ndst=2
    pdst='dst%02d'
    fun  = collate(sequence_key='count', number_per=nper, number_dst=ndst,
                   pattern_dst=pdst)
    counts=[0]*ndst
    for count in range(30):
        msg = Message("src","dst",10*MB,count=count)
        newmsg = fun(msg)
        want = count/nper%ndst
        counts[want] += 1
        dst = pdst%want
        #print newmsg.dst, dst
        assert newmsg.dst == dst
    assert counts[0] == 20
    assert counts[1] == 10
    
def test_dumpmsg():
    fun = dumpmsg(template="#{count} {src}->{dst} {size}")

    msg = Message("src","dst",10*MB,count=0)
    newmsg = fun(msg)

    assert msg.src == newmsg.src
    assert msg.dst == newmsg.dst
    assert msg.size == newmsg.size
    assert msg.count == newmsg.count

def test_compression():
    factor = 5
    fun = compress(factor=str(factor))
    msg = Message("src","dst",10*MB,count=0)
    newmsg = fun(msg)

    assert msg.size == factor*newmsg.size


if '__main__' == __name__:
    test_generate()
    test_robin()
    test_collate()
    test_dumpmsg()
    test_compression()
