DEBUG = False


class RingBuffer(object):
    def __init__(self, size):
        self.buffer = bytearray(size)
        self.start = 0
        self.end = 0

    def __repr__(self):
        return "RingBuffer(start={}, end={}, buffer={})".format(
            self.start, self.end, self.buffer
        )

    def bytes_total(self):
        return len(self.buffer)

    def bytes_used(self):
        if self.start <= self.end:
            return self.end - self.start
        else:
            # we've wrapped, need to add space at end
            end_space = len(self.buffer) - self.start
            # and space used at start
            start_space = self.end
            return end_space + start_space

    def bytes_free(self):
        return self.bytes_total() - self.bytes_used()

    def write(self, bs):
        if len(bs) > self.bytes_free():
            message = "Can't fit {} bytes into buffer ({} used, {} free of total {})".format(
                len(bs), self.bytes_used(), self.bytes_free(), self.bytes_total()
            )
            raise ValueError(message)

        bs_offset = 0
        # first, fit as much as we can into space between end and buffer end
        if self.start <= self.end:  # (only possible if the buffer hasn't wrapped yet)
            offset_start = self.end
            offset_end = min(self.end + len(bs), len(self.buffer))
            bs_offset = offset_end - offset_start
            if DEBUG:
                print("1-writing", bs[:bs_offset], "end is:", offset_end)
            self.buffer[offset_start:offset_end] = bs[:bs_offset]
            self.end = offset_end

        # secondly, fit the remainder at the start of the buffer
        if bs_offset < len(bs):  # (only if there's anything left to write)
            if self.end == len(self.buffer):
                offset_start = 0
            else:
                offset_start = self.end
            offset_end = offset_start + len(bs) - bs_offset
            if DEBUG:
                print("2-writing", bs[bs_offset:])
            self.buffer[offset_start:offset_end] = bs[bs_offset:]
            self.end = offset_end

    def read(self):
        if self.bytes_used() == 0 and items:
            return None

        if self.start < self.end:
            if DEBUG:
                print("1-read")
            offset_start = self.start
            offset_end = self.end
            self.start = self.end
        else:  # buffer has wrapped, so return from start
            if DEBUG:
                print("2-read")
            offset_start = self.start
            offset_end = len(self.buffer)
            self.start = 0
        val = self.buffer[offset_start:offset_end]
        return val
