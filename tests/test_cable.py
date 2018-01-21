import simpy

# this is from the sympy docs.

class Cable(object):
    """This class represents the propagation through a cable."""
    def __init__(self, env, delay):
        self.env = env
        self.delay = delay
        self.store = simpy.Store(env)

    def latency(self, value):
        yield self.env.timeout(self.delay)
        self.store.put(value)

    def put(self, value):
        self.env.process(self.latency(value))

    def get(self):
        return self.store.get()


def sender(env, cable):
    """A process which randomly generates messages."""
    while True:
        # wait for next transmission
        yield env.timeout(5)
        cable.put('Sender sent this at %d' % env.now)


def receiver(env, cable):
    """A process which consumes messages."""
    while True:
        # Get event for message pipe
        msg = yield cable.get()
        print('Received this at %d while %s' % (env.now, msg))


def test():
    # Setup and start the simulation
    print('Event Latency')
    env = simpy.Environment()

    cable = Cable(env, 10)
    env.process(sender(env, cable))
    env.process(receiver(env, cable))

    env.run(until=100)

if __name__ == '__main__':
    test()
    
