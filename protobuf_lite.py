#!/usr/bin/env python3
"""protobuf_lite - Minimal protobuf-style varint and wire format encoder/decoder."""
import sys, struct

def encode_varint(n):
    if n < 0: n = n + (1 << 64)
    buf = []
    while n > 0x7f:
        buf.append((n & 0x7f) | 0x80)
        n >>= 7
    buf.append(n)
    return bytes(buf)

def decode_varint(data, offset=0):
    result, shift = 0, 0
    while True:
        b = data[offset]
        result |= (b & 0x7f) << shift
        offset += 1
        if not (b & 0x80): break
        shift += 7
    return result, offset

def encode_field(field_num, wire_type, data):
    tag = (field_num << 3) | wire_type
    return encode_varint(tag) + data

def encode_message(fields):
    """fields: [(field_num, value)] where value is int or bytes/str."""
    buf = b""
    for num, val in fields:
        if isinstance(val, int):
            buf += encode_field(num, 0, encode_varint(val))
        elif isinstance(val, (bytes, str)):
            b = val.encode() if isinstance(val, str) else val
            buf += encode_field(num, 2, encode_varint(len(b)) + b)
    return buf

def decode_message(data):
    fields = []
    i = 0
    while i < len(data):
        tag, i = decode_varint(data, i)
        field_num = tag >> 3
        wire_type = tag & 0x07
        if wire_type == 0:
            val, i = decode_varint(data, i)
            fields.append((field_num, val))
        elif wire_type == 2:
            length, i = decode_varint(data, i)
            fields.append((field_num, data[i:i+length]))
            i += length
        else:
            raise ValueError(f"Unsupported wire type {wire_type}")
    return fields

def test():
    assert encode_varint(1) == b"\x01"
    assert encode_varint(300) == b"\xac\x02"
    v, _ = decode_varint(encode_varint(300))
    assert v == 300
    v2, _ = decode_varint(encode_varint(0))
    assert v2 == 0
    msg = encode_message([(1, 42), (2, "hello"), (3, 1000)])
    fields = decode_message(msg)
    assert (1, 42) in fields
    assert (2, b"hello") in fields
    assert (3, 1000) in fields
    print("protobuf_lite: all tests passed")

if __name__ == "__main__":
    test() if "--test" in sys.argv else print("Usage: protobuf_lite.py --test")
