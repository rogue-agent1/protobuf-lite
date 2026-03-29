#!/usr/bin/env python3
"""protobuf_lite: Minimal Protocol Buffers wire format encoder/decoder."""
import struct, sys

def encode_varint(n):
    if n < 0: n = n + (1 << 64)
    result = bytearray()
    while n > 0x7F:
        result.append((n & 0x7F) | 0x80)
        n >>= 7
    result.append(n & 0x7F)
    return bytes(result)

def decode_varint(data, offset=0):
    result, shift = 0, 0
    while True:
        b = data[offset]
        result |= (b & 0x7F) << shift
        offset += 1
        if not (b & 0x80): break
        shift += 7
    return result, offset

def encode_field(field_num, wire_type, value):
    tag = encode_varint((field_num << 3) | wire_type)
    if wire_type == 0:  # varint
        return tag + encode_varint(value)
    elif wire_type == 2:  # length-delimited
        if isinstance(value, str): value = value.encode()
        return tag + encode_varint(len(value)) + value
    elif wire_type == 1:  # 64-bit
        return tag + struct.pack("<d", value)
    elif wire_type == 5:  # 32-bit
        return tag + struct.pack("<f", value)
    raise ValueError(f"Unknown wire type {wire_type}")

def decode_fields(data):
    fields = []
    offset = 0
    while offset < len(data):
        tag, offset = decode_varint(data, offset)
        field_num = tag >> 3
        wire_type = tag & 0x07
        if wire_type == 0:
            value, offset = decode_varint(data, offset)
        elif wire_type == 2:
            length, offset = decode_varint(data, offset)
            value = data[offset:offset+length]
            offset += length
        elif wire_type == 1:
            value = struct.unpack("<d", data[offset:offset+8])[0]
            offset += 8
        elif wire_type == 5:
            value = struct.unpack("<f", data[offset:offset+4])[0]
            offset += 4
        else:
            raise ValueError(f"Unknown wire type {wire_type}")
        fields.append((field_num, wire_type, value))
    return fields

def encode_message(fields_dict):
    result = b""
    for (field_num, wire_type), value in sorted(fields_dict.items()):
        result += encode_field(field_num, wire_type, value)
    return result

def test():
    # Varint
    for n in [0, 1, 127, 128, 300, 16384]:
        enc = encode_varint(n)
        dec, _ = decode_varint(enc)
        assert dec == n, f"{n} -> {dec}"
    # Fields
    msg = encode_message({
        (1, 0): 150,       # field 1, varint
        (2, 2): "testing", # field 2, string
        (3, 1): 3.14,      # field 3, double
    })
    fields = decode_fields(msg)
    assert len(fields) == 3
    assert fields[0] == (1, 0, 150)
    assert fields[1] == (2, 2, b"testing")
    assert abs(fields[2][2] - 3.14) < 1e-9
    # Nested message
    inner = encode_message({(1, 0): 42})
    outer = encode_message({(1, 2): inner, (2, 0): 1})
    decoded = decode_fields(outer)
    inner_fields = decode_fields(decoded[0][2])
    assert inner_fields[0] == (1, 0, 42)
    print("All tests passed!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test": test()
    else: print("Usage: protobuf_lite.py test")
