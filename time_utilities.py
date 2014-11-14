from datetime import datetime
from uuid import uuid1, UUID
import random

def _timestamp_to_uuid(time_arg):
    # TODO: once this is in the python Cassandra driver, use that
    microseconds = int(time_arg * 1e6)
    timestamp = int(microseconds * 10) + 0x01b21dd213814000L

    time_low = timestamp & 0xffffffffL
    time_mid = (timestamp >> 32L) & 0xffffL
    time_hi_version = (timestamp >> 48L) & 0x0fffL

    rand_bits = random.getrandbits(8 + 8 + 48)
    clock_seq_low = rand_bits & 0xffL
    clock_seq_hi_variant = 0b10000000 | (0b00111111 & ((rand_bits & 0xff00L) >> 8))
    node = (rand_bits & 0xffffffffffff0000L) >> 16
    return UUID(
        fields=(time_low, time_mid, time_hi_version, clock_seq_hi_variant, clock_seq_low, node),
        version=1)

