import simpy

def dump(env, me, msg):
    print ('%6.1f\t%s:\t%s' % (env.now, me, msg))


def write_to_queue(env, lock, queue, start, me):
    for count in range(start, start+5):
        with lock.request() as req:
            yield req
            yield env.timeout(1)
            msg = (env.now,count)
            dump(env, me, msg)
            yield queue.put(msg)
            yield env.timeout(1)

def copy_to_queue(env, inlock, inqueue, outlock, outqueue, me):
    while True:
        with inlock.request() as rreq:
            yield rreq
            with outlock.request() as wreq:
                yield wreq
                msg = yield inqueue.get()
                yield env.timeout(10)
                dump(env, me, msg)
                outqueue.put(msg)
            

def reader(env, queue, bufsize, me):
    while True:
        buf = list()
        for i in range(bufsize):
            d = yield queue.get()
            buf.append(d)
        yield env.timeout(1)
        dump(env, me, buf)

def main():
    env = simpy.Environment()
    wlock = simpy.Resource(env, 1)
    rlock = simpy.Resource(env, 1)
    queue = simpy.Store(env)
    outlock = simpy.Resource(env, 1)
    outqueue = simpy.Store(env)

    env.process(write_to_queue(env, wlock, queue, 1, 'w1'))
    env.process(write_to_queue(env, wlock, queue, 10, 'w2'))
    env.process(write_to_queue(env, wlock, queue, 100, 'w3'))
    env.process(copy_to_queue(env, rlock, queue, outlock, outqueue, 'c1'))
    env.process(copy_to_queue(env, rlock, queue, outlock, outqueue, 'c2'))
    env.process(reader(env, outqueue, 2, 'r1'))
    env.process(reader(env, outqueue, 3, 'r2'))
    SIM_DURATION = 500
    env.run(until=SIM_DURATION)



if '__main__' == __name__:
    main()
