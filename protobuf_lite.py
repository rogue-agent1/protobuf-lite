#!/usr/bin/env python3
"""Minimal protobuf wire format encoder/decoder."""

def _encode_varint(value):
    result = bytearray()
    while value > 0x7f:
        result.append((value & 0x7f) | 0x80)
        value >>= 7
    result.append(value & 0x7f)
    return bytes(result)

def _decode_varint(data, pos):
    result = 0; shift = 0
    while True:
        b = data[pos]; pos += 1
        result |= (b & 0x7f) << shift
        if not (b & 0x80): break
        shift += 7
    return result, pos

def encode_field(field_num, wire_type, value):
    tag = _encode_varint((field_num << 3) | wire_type)
    if wire_type == 0:  # varint
        return tag + _encode_varint(value)
    elif wire_type == 2:  # length-delimited
        if isinstance(value, str): value = value.encode()
        return tag + _encode_varint(len(value)) + value
    raise ValueError(f"Unsupported wire type {wire_type}")

def decode_fields(data: bytes) -> list:
    fields = []; pos = 0
    while pos < len(data):
        tag, pos = _decode_varint(data, pos)
        field_num = tag >> 3; wire_type = tag & 0x07
        if wire_type == 0:
            value, pos = _decode_varint(data, pos)
        elif wire_type == 2:
            length, pos = _decode_varint(data, pos)
            value = data[pos:pos+length]; pos += length
        elif wire_type == 5:
            import struct
            value = struct.unpack("<I", data[pos:pos+4])[0]; pos += 4
        elif wire_type == 1:
            import struct
            value = struct.unpack("<Q", data[pos:pos+8])[0]; pos += 8
        else:
            raise ValueError(f"Unknown wire type {wire_type}")
        fields.append((field_num, wire_type, value))
    return fields

class Message:
    def __init__(self):
        self._fields = {}
    def set_varint(self, num, val): self._fields[num] = (0, val)
    def set_string(self, num, val): self._fields[num] = (2, val)
    def set_bytes(self, num, val): self._fields[num] = (2, val)
    def encode(self) -> bytes:
        return b"".join(encode_field(num, wt, val) for num, (wt, val) in sorted(self._fields.items()))
    @classmethod
    def decode(cls, data: bytes):
        m = cls(); fields = decode_fields(data)
        for num, wt, val in fields:
            m._fields[num] = (wt, val)
        return m
    def get(self, num, default=None):
        if num in self._fields: return self._fields[num][1]
        return default

if __name__ == "__main__":
    m = Message()
    m.set_varint(1, 42)
    m.set_string(2, "hello")
    data = m.encode()
    print(f"Encoded ({len(data)} bytes): {data.hex()}")
    m2 = Message.decode(data)
    print(f"Field 1: {m2.get(1)}, Field 2: {m2.get(2)}")

def test():
    # Varint encoding
    assert _encode_varint(0) == b"\x00"
    assert _encode_varint(1) == b"\x01"
    assert _encode_varint(300) == b"\xac\x02"
    # Round-trip
    m = Message()
    m.set_varint(1, 150)
    m.set_string(2, "testing")
    data = m.encode()
    m2 = Message.decode(data)
    assert m2.get(1) == 150
    assert m2.get(2) == b"testing"
    # Multiple fields
    m3 = Message()
    m3.set_varint(1, 0)
    m3.set_varint(3, 999)
    m3.set_string(5, "end")
    d = m3.encode()
    m4 = Message.decode(d)
    assert m4.get(1) == 0
    assert m4.get(3) == 999
    print("  protobuf_lite: ALL TESTS PASSED")
