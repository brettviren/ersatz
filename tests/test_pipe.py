import simpy
import random

from ersatz.net import Pipe, Message
from ersatz import units

def producer(env, pipe):
    count = 0
    while True:
        tx = yield pipe.send()
        msg = Message("producer","consumer",units.GB,
                      count=count, time=env.now)
        print ('-> put: %d %s' % (env.now,str(msg)))
        count += 1
        tx.put(msg)


def consumer(env, pipe):
    count = 0
    while True:
        rx = yield pipe.recv()
        msg = rx.get()
        print ('<- get: %d %s' % (env.now, str(msg)))
        assert (count == msg.count)
        count += 1
        #yield env.timeout(random.randint(4, 8))
        yield env.timeout(10)


def test_main():
    env = simpy.Environment()
    pipe = Pipe(env, delay=1, bandwidth=units.Gbps)
    env.process(producer(env, pipe))
    env.process(consumer(env, pipe))

    env.run(until=100)


if '__main__' == __name__:
    test_main()
    
