import unittest
import random
import itertools
import string
import traceback

from ring_buffer import RingBuffer


class TestRingBuffer(unittest.TestCase):
    def test_basic(self):
        b = RingBuffer(6)
        b.write(b"abc")
        self.assertEqual(b.read(), b"abc")
        self.assertEqual(b.read(), None)

    def test_basic_two(self):
        b = RingBuffer(6)
        b.write(b"abc")
        b.write(b"de")
        self.assertEqual(b.read(), b"abcde")
        self.assertEqual(b.read(), None)

    def test_basic_wrap(self):
        b = RingBuffer(4)
        b.write(b"ab")
        self.assertEqual(b.read(), b"ab")
        self.assertEqual(b.bytes_used(), 0)
        b.write(b"cde")
        self.assertEqual(b.read(), b"cd")
        self.assertEqual(b.read(), b"e")
        self.assertEqual(b.read(), None)

    def test_size_zero_buffer(self):
        b = RingBuffer(0)
        self.assertEqual(b.bytes_total(), 0)
        self.assertEqual(b.bytes_free(), 0)
        self.assertEqual(b.bytes_used(), 0)
        with self.assertRaises(ValueError):
            b.write(b"a")

    def test_size_one_buffer(self):
        b = RingBuffer(1)
        self.assertEqual(b.bytes_total(), 1)
        self.assertEqual(b.bytes_free(), 1)
        self.assertEqual(b.bytes_used(), 0)

        b.write(b"a")
        self.assertEqual(b.bytes_total(), 1)
        self.assertEqual(b.bytes_free(), 0)
        self.assertEqual(b.bytes_used(), 1)

        self.assertEqual(b.read(), b"a")
        self.assertEqual(b.bytes_total(), 1)
        self.assertEqual(b.bytes_free(), 1)
        self.assertEqual(b.bytes_used(), 0)

        self.assertEqual(b.read(), None)

        b.write(b"b")
        self.assertEqual(b.read(), b"b")
        self.assertEqual(b.read(), None)

    def test_size_wrap_and_full(self):
        b = RingBuffer(2)

        b.write(b"a")
        self.assertEqual(b.read(), b"a")
        self.assertEqual(b.read(), None)

        b.write(b"bc")
        self.assertEqual(b.read(), b"b")
        self.assertEqual(b.read(), b"c")
        self.assertEqual(b.read(), None)

    def test_read_empty(self):
        b = RingBuffer(6)
        self.assertEqual(b.read(), None)

    def test_write_empty(self):
        b = RingBuffer(6)
        b.write(b"")
        self.assertEqual(b.bytes_used(), 0)
        self.assertEqual(b.read(), None)

    def test_writing_respects_overall_size(self):
        b = RingBuffer(4)
        with self.assertRaises(ValueError):
            b.write(b"abcde")

    def test_writing_respects_bytes_used(self):
        b = RingBuffer(4)
        b.write(b"ab")
        with self.assertRaises(ValueError):
            b.write(b"cde")

    def test_random_operations(self):
        """A quicktest-lite test to verify various operations work as intended"""
        debug_this = False

        for test_num in range(1000):
            inputs = itertools.cycle(string.ascii_letters.encode("ascii"))

            # params for test
            operation_count = random.randrange(1, 20)
            # possible operations: None = read input, number = write that many bytes
            operations = random.choices([None] + list(range(1, 5)), k=operation_count)
            buffer_size = random.randrange(20)

            # do the test
            buffer = RingBuffer(buffer_size)
            read_from_buffer = bytearray()
            backup = bytearray()
            read_from_backup = bytearray()
            for op_i, op in enumerate(operations):
                try:
                    if debug_this:
                        print("doing op", op)
                    if op is None:
                        # slurp all items from buffer
                        while True:
                            last_read = buffer.read()
                            if debug_this:
                                print("read from buffer", last_read)
                            if last_read is None:
                                break
                            else:
                                read_from_buffer.extend(last_read)

                        # slurp all items from backup
                        read_from_backup.extend(backup)
                        backup.clear()
                    else:
                        # check we can't write more than we have space for
                        if len(backup) + op > buffer_size:
                            with self.assertRaises(ValueError):
                                items_to_write = list(itertools.islice(inputs, op))
                                buffer.write(items_to_write)

                        # actually try and write no more than we have space for
                        count_to_write = min(op, buffer_size - len(backup))
                        items_to_write = bytes(
                            list(itertools.islice(inputs, count_to_write))
                        )
                        if debug_this:
                            print("to_write", items_to_write)
                        buffer.write(items_to_write)
                        backup.extend(items_to_write)
                        if debug_this:
                            print("buffer:", buffer)
                    self.assertEqual(read_from_buffer, read_from_backup)
                except AssertionError as e:
                    message = e.args[0]
                    message += "\nFailed on test number {}".format(test_num)
                    message += "\nOperation: #{op_i} ('{op}')".format(op_i=op_i, op=op)
                    message += "\nParams:\n\toperations={operations}\n\tbuffer_size={buffer_size}".format(
                        operations=operations, buffer_size=buffer_size
                    )
                    message += "\nState:\n\tbuffer={buffer}\n\tbackup={backup}".format(
                        buffer=buffer, backup=backup
                    )
                    e.args = (message,)
                    raise


if __name__ == "__main__":
    unittest.main()

