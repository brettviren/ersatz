import simpy
from ersatz.graph import InPort

def sender(env, port):
    for count in range(5):
        yield env.timeout(units.second)
        msg = Message(None, None, units.GB, sent=env.now, count=count)
        port.put(msg)
        print ('sent %d at %f' % (count, msg.sent))


def receiver(env, port):
    while True:
        msg = yield port.get()
        print('recv %d at %f in %f seconds' % (msg.count, env.now, env.now - msg.sent))



def test_port():
    env = simpy.Environment()
    port = Port(env)
    env.process(sender(env, port))
    env.process(receiver(env, port))
    SIM_DURATION = 100
    env.run(until=SIM_DURATION)
    
