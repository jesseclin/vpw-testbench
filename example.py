#!/usr/bin/env python3
"""
Example testbench
"""

import vpw
import vpw.axis
import vpw.axim
import vpw.axim2ram

import random

if __name__ == '__main__':

    dut = vpw.create(module='example',
                     clock='clk')
    vpw.init(dut)

    up_stream = vpw.axis.Master("up_axis", 32, concat=2)
    vpw.register(up_stream)

    dn_stream = vpw.axis.Slave("dn_axis", 32, concat=2)
    vpw.register(dn_stream)

    axim = vpw.axim.Master("axim", 128, 16)
    vpw.register(axim)

    vpw.register(vpw.axim2ram.Memory("axim2ram", 128, 16))

    # test AXI-Streaming interface
    data1 = [n+1 for n in range(16)]
    data2 = [17, 18, 19, 20, 21, 22, 23, 24]
    up_stream.send(data1, position=0)
    up_stream.send(data2, position=1)

    dn_stream.ready(True, position=0)
    dn_stream.ready(True, position=1)

    vpw.idle(100)

    print("First stream received")
    stream = dn_stream.recv(position=0)
    for x in stream:
        print(f"stream 1: {x}")

    print("Second stream received")
    stream = dn_stream.recv(position=1)
    for x in stream:
        print(f"stream 2: {x}")

    print("Intermittent ready on down stream receive")
    up_stream.send([n+1 for n in range(10)], position=0)
    while len(dn_stream.queue[0]) == 0:
        dn_stream.ready(bool(random.getrandbits(1)))
        vpw.tick()

    stream = dn_stream.recv(position=0)
    for x in stream:
        print(f"intermittent 0: {x}")

    vpw.idle(100)

    print("Intermittent valid on up stream send")
    up_stream.send([n+1 for n in range(10)], position=1)
    while len(dn_stream.queue[1]) == 0:
        up_stream.pause(bool(random.getrandbits(1)), 1)
        vpw.tick()

    stream = dn_stream.recv(position=1)
    for x in stream:
        print(f"intermittent 1: {x}")

    # test AXI-MM interface
    axim.send_write(0, [n+1 for n in range(128)])

    vpw.idle(1000)

    axim.send_read(0, 128)

    while True:
        vpw.tick()
        burst = axim.recv_read()
        if burst:
            print(burst)
            for x, beat in enumerate(burst):
                assert((x+1) == beat)

            break

    vpw.idle(10)

    # test AXI-MM interface with large write/read pair
    data = [n+1 for n in range(512)]
    axim.write(vpw.tick, 256, data, 1)

    received = axim.read(vpw.tick, 256, int(len(data) * 128 / 8), 1)

    for s, r in zip(data, received):
        assert(s == r)

    vpw.idle(100)

    vpw.finish()
