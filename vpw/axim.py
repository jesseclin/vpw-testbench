"""
AXIM Master Interface
"""

from typing import Generator
from typing import Optional
from typing import Deque
from typing import List
from typing import Dict
from typing import Any

from math import ceil
from collections import deque


class Master:
    def __init__(self, interface: str, data_width: int, addr_width: int) -> None:
        assert((data_width % 8) == 0)
        assert(addr_width <= 64)
        self.interface = interface
        self.data_width = data_width
        self.addr_width = addr_width

        # read data channel, queues contained in list addressable via (A)RID
        self.queue_r: List[Deque[List[int]]] = [deque() for _ in range(16)]

        # read address channel
        self.queue_ar: Deque[Dict[str, Any]] = deque()

        # keep track of lengths of requested read bursts, list addressable via (A)RID
        self.pending_ar: List[Deque[int]] = [deque() for _ in range(16)]

    def __pack(self, val: int) -> List[int]:
        if self.data_width <= 64:
            return [val]
        else:
            start = ceil(self.data_width / 32)
            shift = [32*s for s in range(start)]
            return [((val >> s) & 0xffffffff) for s in shift]

    def __unpack(self, val: List[int]) -> int:
        if self.data_width <= 64:
            return val[0]
        else:
            start = ceil(self.data_width / 32)
            shift = [32*s for s in range(start)]
            number: int = 0
            for v, s in zip(val, shift):
                number = number | (v << s)

            return number

    def __r(self) -> Generator:
        burst_id: int = 0

        # store current burst of data being received
        burst_data: List[int] = []

        # setup
        self.__dut.prep(f"{self.interface}_rready", [1])

        while True:
            io = yield

            if io[f"{self.interface}_rready"] and io[f"{self.interface}_rvalid"]:
                data = self.__unpack(io[f"{self.interface}_rdata"])
                burst_data.append(data)

                if len(burst_data) == 1:
                    # first beat of a burst
                    burst_id = io[f"{self.interface}_rid"]

                    # check that there exists a pending read with the same ID
                    assert(self.pending_ar[burst_id])
                else:
                    # check that beat ID is consistent with the bursts
                    assert(burst_id == io[f"{self.interface}_rid"])

                if io[f"{self.interface}_rlast"]:
                    # check that received burst is the length requested
                    assert(self.pending_ar[burst_id][0] == len(burst_data))

                    self.queue_r[burst_id].append(burst_data)
                    self.pending_ar[burst_id].popleft()
                    burst_data = []

    def __ar(self) -> Generator:

        while True:
            if not self.queue_ar:
                self.__dut.prep(f"{self.interface}_araddr", [0])
                self.__dut.prep(f"{self.interface}_arlen", [0])
                self.__dut.prep(f"{self.interface}_arid", [0])
                self.__dut.prep(f"{self.interface}_arvalid", [0])
                io = yield
            else:
                current_ar: Dict[str, Any] = self.queue_ar[0]

                self.__dut.prep(f"{self.interface}_araddr", [current_ar["araddr"]])
                self.__dut.prep(f"{self.interface}_arlen", [current_ar["arlen"]])
                self.__dut.prep(f"{self.interface}_arid", [current_ar["arid"]])
                self.__dut.prep(f"{self.interface}_arvalid", [1])

                io = yield
                while io[f"{self.interface}_arready"] == 0:
                    io = yield

                self.pending_ar[current_ar["arid"]].append(current_ar["arlen"] + 1)
                self.queue_ar.popleft()

    def send_read(self, addr: int, length: int, read_id: int = 0) -> None:
        """
        Non-Blocking: Queue a burst address to send, the address is in bytes
        but must be AXIM word aligned as must the length. The length must also
        respect the 4KB boundaries as per the AXI spec.
        """
        assert((addr % self.data_width) == 0)
        assert((length % self.data_width) == 0)
        assert(((addr % 4096) + length) <= 4096)
        self.queue_ar.append({"araddr": addr,
                              "arlen": int((8 * length / self.data_width) - 1),
                              "arid": read_id})

    def recv_read(self, read_id: int = 0) -> Optional[List[int]]:
        """
        Non-Blocking: Returns a burst of received data contained in a list, one
        beat per list elsement.
        """
        if not self.queue_r[read_id]:
            return None
        else:
            return self.queue_r[read_id].popleft()

    def init(self, dut) -> Generator:
        self.__dut = dut

        ch_r = self.__r()
        ch_ar = self.__ar()

        next(ch_r)
        next(ch_ar)

        while True:
            io = yield

            ch_r.send(io)
            ch_ar.send(io)
