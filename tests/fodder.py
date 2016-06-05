cfgstr = '''
[network net1]
routers = router1, router2

[router router1]
layers = layer1, layer2
bandwidth = 1*Gbps
delay = 10*ms

[router router2]
layers = layer2, layer3
bandwidth = 1*Gbps
delay = 10*ms


[layer layer1]
nhosts = 10
hostname = gen%02d
pipeline = generate, roundrobin

[layer layer2]
nhosts = 5
hostname = mid%02d
pipeline = compress,collate

[layer layer3]
nhosts = 10
hostname = fin%02d
pipeline = dumpmsg


[function generate]
rate = 10*Hz
size = 10*MB

[function roundrobin]
sequence_key = seqno
number_dst = 10
pattern_dst = mid%02d

[function compress]
factor = 5

[function collate]
sequence_key = seqno
number_per = 1000
number_dst = 10
pattern_dst = fin%02d

[function dumpmsg]
message = {src} -> {dst} size={size} count={count}

'''
