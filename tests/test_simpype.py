import simpype
import random
sim = simpype.Simulation(id = 'overview')
gen0 = sim.add_generator(id = 'gen0')
gen0.random['arrival'] = {0: lambda: random.expovariate(1.0)}
res0 = sim.add_resource(id = 'res0')
res0.random['service'] = {0: lambda: random.expovariate(2.0)}
p0 = sim.add_pipeline(gen0, res0)
sim.run(until = 10)

