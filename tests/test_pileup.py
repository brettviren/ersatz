#!/usr/bin/env python3

import simpy

def dump_job(now, name, job, msg=""):
    print ("%8.2f %8s %s %s" % (now, name, job, msg))

class MiddleMan(object):
    def __init__(self, env):
        self.env = env
        self.jobs = dict()
        self.waiting = set()
        self.inbox = simpy.Store(env)
        self.outbox = simpy.Store(env)
        self.worker = simpy.PreemptiveResource(env, capacity=1)
        env.process(self.work())

    def work(self):
        while True:
            job = yield self.inbox.get()    
            self.env.process(self.dojob(job))

    def update(self, elapsed):
        for job in self.jobs.values():
            job.update(elapsed)

    def find_next(self):
        if not self.jobs:
            return None
        l = list(self.jobs.values())
        l.sort()
        return l[0]

    def find_done(self):
        return [job for job in self.jobs.values() if job.done]

    def dojob(self, job):
        prio = -1*len(self.jobs)
        dump_job(self.env.now, "dojob", job, "%d left" % len(self.jobs))
        self.waiting.add(job)
        with self.worker.request(priority=prio) as req: # this prempts any existing job
            yield req
            for job in self.waiting:
                self.jobs[job.ident] = job
            self.waiting = set()
            job = self.find_next()
            if not job:
                return
            start = self.env.now
            try:
                dump_job(self.env.now, "doing", job, "%d left" % len(self.jobs))
                yield self.env.timeout(job.eta)
            except simpy.Interrupt: # someone else came to deliver
                elapsed = self.env.now-start
                dump_job(self.env.now, "inter", job, "%d left" % len(self.jobs))
                self.update(elapsed)
                for j in self.find_done():
                    dump_job(self.env.now, "DONE", j, "%d left" % len(self.jobs))
                    self.jobs.pop(j.ident)
                    yield self.outbox.put(j)
                    continue
                return

            # reach here, successfully waited out a stream to finish
            elapsed = self.env.now - start
            self.update(elapsed)
            for j in self.find_done():
                dump_job(self.env.now, "DONE", j, "%d left" % len(self.jobs))
                self.jobs.pop(j.ident)
                yield self.outbox.put(j)
                continue
            pass
        job = self.find_next()
        dump_job(self.env.now, "next", job)
        if job:
            self.env.process(self.dojob(job))


class Job(object):
    epsilon = 1e-3

    def __init__(self, ident, rate, amount):
        self.ident = ident
        self.rate = float(rate)
        self.remaining = float(amount)
        self.amount = float(amount)

    @property
    def done(self):
        if abs(self.eta) < self.epsilon:
            return True
        return False

    @property
    def eta(self):
        ret = self.remaining / self.rate
        if abs(ret) < self.epsilon:
            return 0.0
        if ret<0:
            print ("remaining=%f, rate=%f" %( self.remaining, self.rate))
        return ret

    def update(self, elapsed):
        '''
        Update remaining assuming elapsed time since last update.
        '''
        delta = self.rate*elapsed
        self.remaining -= delta
        if abs(self.remaining) < self.epsilon:
            self.remaining = 0.0
        if self.remaining < 0:
            dump_job (0, "error", self, "delta=%f, elapsed=%f" % (delta, elapsed))
            raise ValueError("overly depleted: elapsed=%f, rate=%f, delta=%f, remaining=%f" % (elapsed, self.rate, delta, self.remaining))

    def __str__(self):
        return "job #%02d %.2f%% eta:%.2f" % (self.ident, 100.0*self.remaining/self.amount, self.eta )

    def __lt__(self, other):
        if self.ident == other.ident:
            return False
        if self.remaining == other.remaining:
            return self.ident < other.ident
        return self.remaining < other.remaining

def job_feeder(env, inbox, rate, amount, nsimu=5):
    count = 0
    for rounds in range(2):
        yield env.timeout(1)
        for n in range(nsimu):
            job = Job(count, rate, amount)
            count += 1
            dump_job(env.now, "make", job, "nmade=%d" % count)
            yield inbox.put(job)

def job_finisher(env, outbox):
    ndone = 0;
    while True:
        job = yield outbox.get()
        ndone += 1
        dump_job(env.now, "done", job, "ndone=%d"%ndone)

def test_pileup():

    env = simpy.Environment()
    mm = MiddleMan(env)

    env.process(job_feeder(env, mm.inbox, 0.1, 10.0))
    env.process(job_finisher(env, mm.outbox))

    env.run(until=200.0)

if '__main__' == __name__:
    test_pileup()
    
