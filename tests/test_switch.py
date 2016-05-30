from collections import namedtuple
import simpy
from ersatz import net, units

def client_send(env, tx, size=units.GB,
                client="client1", server="server1", pause=3):
    for count in range(5):
        yield env.timeout(pause)
        print('%f %s send %d to %s' % (env.now, client, count, server))
        tx.put(net.Message(client, server, size, count=count, start=env.now))

def client_recv(env,rx):
    while True:
        msg = yield rx.get()
        print('%f %s recv %d from %s ping %f' %
              (env.now, msg.dst, msg.count, msg.src, env.now-msg.start))

def server_listen(env, nic, size=units.GB):
    while True:
        msg = yield nic.rx.get()
        print ('%f %s got %d from %s' %
               (env.now, msg.dst, msg.count, msg.src))

        newmsg = net.Message(msg.dst, msg.src, size,
                             count=msg.count, start=msg.start)
        nic.tx.put(newmsg)

Packet = namedtuple('Packet','ctx time msg')
class PacketCapture(object):
    def __init__(self, env):
        self.env = env
        self.history = list()

    def capture(self, ctx, msg): 
        self.history.append(Packet(ctx, self.env.now, msg))

    def rx(self, msg):
        self.capture('rx', msg)
    def tx(self, msg):
        self.capture('tx', msg)
    def switch(self, msg):
        self.capture('switch', msg)
        
    def sequence_diagram(self, clients, servers):
        "Return seqdiag string."
        lines = ["diagram {"]
        for pac in self.history:

            if pac.ctx == 'rx': # receive
                name = pac.msg.dst
                if name in clients:
                    arrow = "%s <-- switch_%s" % (name, name)
                if name in servers:
                    arrow = "switch_%s -> %s" % (name, name)

            if pac.ctx == 'tx': # transmit
                name = pac.msg.src
                if name in clients:
                    arrow = "%s -> switch_%s" % (name, name)
                if name in servers:
                    arrow = "switch_%s <-- %s" % (name, name)

            if pac.ctx == 'switch':
                src = 'switch_' + pac.msg.src
                dst = 'switch_' + pac.msg.dst

                if pac.msg.src in clients:
                    arrow = "%s -> %s" % (src, dst)
                if pac.msg.src in servers:
                    arrow = "%s <-- %s" % (dst, src)


            lines.append('%s[label="#%d %s:%s %s"];' %
                         (arrow,
                          pac.msg.count, pac.msg.src, pac.msg.dst,
                          units.bytes_str(pac.msg.size)))
        lines.append("}")
        return "\n".join(lines)
        
def do_switch(nclients, nservers):

    env = simpy.Environment()

    cap = PacketCapture(env)

    sw = net.Switch(env, units.Gbps, inspector = cap.switch)

    client_nic = list()
    for ind in range(nclients):
        nic = net.NIC(env, (ind+1)*10*units.ms,
                      rxinspector=cap.rx, txinspector=cap.tx)
        sw.conn("client%d"%ind, nic)
        client_nic.append(nic)

    server_nic = list()
    for ind in range(nservers):
        nic = net.NIC(env, (ind+1)*100*units.ms,
                      rxinspector=cap.rx, txinspector=cap.tx)
        sw.conn("server%d"%ind, nic)
        server_nic.append(nic)

    # Make each client send to each server with progressively larger payloads
    for iclient, client in enumerate(client_nic):
        for iserver in range(nservers):
            env.process(client_send(env, client.tx, (iclient+1)*units.GB,
                                    "client%d"%iclient, "server%d"%iserver))

    # set client receivers
    for client in client_nic:
        env.process(client_recv(env, client.rx))

    # make servers
    for iserver,server in enumerate(server_nic):
        env.process(server_listen(env, server, (iserver+1)*units.kB))


    SIM_DURATION = 500
    env.run(until=SIM_DURATION)

    with open("test_switch_c%d_s%d.diag" % (nclients, nservers),"w") as fp:
        fp.write(cap.sequence_diagram(['client%d'%c for c in range(nclients)],
                                      ['server%d'%s for s in range(nservers)]))

def test_21():
    do_switch(2,1)

if '__main__' == __name__:
    do_switch(1,1)
    
