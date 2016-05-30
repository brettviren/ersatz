import simpy
from ersatz.net import Link, Message
from ersatz import units

def sender(env, link):
    """A simple process which randomly generates messages."""
    for count in range(5):
        yield env.timeout(units.second)
        msg = Message(None, None, units.GB, sent=env.now, count=count)
        link.put(msg)
        print ('sent %d at %f' % (count, msg.sent))


def receiver(env, link):
    """A process which consumes messages."""
    while True:
        msg = yield link.get()
        print('recv %d at %f in %f seconds' % (msg.count, env.now, env.now - msg.sent))


def test_sender_receiver():

    env = simpy.Environment()
    link = Link(env, 10*units.second)
    env.process(sender(env, link))
    env.process(receiver(env, link))
    SIM_DURATION = 100
    env.run(until=SIM_DURATION)

if '__main__' == __name__:
    test_sender_receiver()
    
