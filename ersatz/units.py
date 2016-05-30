# some units
bit=1
second=1

millisecond=1e-3*second
microsecond=1e-6*second
nanosecond=1e-9*second
ms=millisecond
us=microsecond
ns=nanosecond


baud=bit/second

Byte=8*bit
kB=1e3*Byte
MB=1e6*Byte
GB=1e9*Byte
Gbit=1e9*bit
Gbps=1e9*baud

def bytes_str(B):
    if B < 1e3:
        return "%d B" % (B/Byte,)
    if B < 1e6:
        return "%.1f kB" % (B/kB,)
    if B < 1e9:
        return "%.1f MB" % (B/MB,)
    return "%.1f GB" % (B/1.0e9,)
