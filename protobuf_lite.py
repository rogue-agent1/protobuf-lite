#!/usr/bin/env python3
"""Protobuf-like encoder/decoder. Zero dependencies."""
import struct, sys

VARINT = 0; I64 = 1; LEN = 2; I32 = 5

def encode_varint(value):
    if value < 0: value = value & 0xFFFFFFFFFFFFFFFF
    result = bytearray()
    while value > 0x7F:
        result.append((value & 0x7F) | 0x80); value >>= 7
    result.append(value & 0x7F)
    return bytes(result)

def decode_varint(data, offset=0):
    result = 0; shift = 0
    while offset < len(data):
        b = data[offset]; offset += 1
        result |= (b & 0x7F) << shift; shift += 7
        if not (b & 0x80): break
    return result, offset

def encode_field(field_num, wire_type, value):
    tag = encode_varint((field_num << 3) | wire_type)
    if wire_type == VARINT: return tag + encode_varint(value)
    if wire_type == LEN:
        if isinstance(value, str): value = value.encode()
        return tag + encode_varint(len(value)) + value
    if wire_type == I32: return tag + struct.pack("<I", value)
    if wire_type == I64: return tag + struct.pack("<Q", value)
    return tag

def decode_message(data):
    fields = {}; offset = 0
    while offset < len(data):
        tag, offset = decode_varint(data, offset)
        field_num = tag >> 3; wire_type = tag & 0x07
        if wire_type == VARINT:
            value, offset = decode_varint(data, offset)
        elif wire_type == LEN:
            length, offset = decode_varint(data, offset)
            value = data[offset:offset+length]; offset += length
            try: value = value.decode()
            except: pass
        elif wire_type == I32:
            value = struct.unpack_from("<I", data, offset)[0]; offset += 4
        elif wire_type == I64:
            value = struct.unpack_from("<Q", data, offset)[0]; offset += 8
        else: break
        if field_num in fields:
            if not isinstance(fields[field_num], list):
                fields[field_num] = [fields[field_num]]
            fields[field_num].append(value)
        else:
            fields[field_num] = value
    return fields

def encode_message(fields):
    result = bytearray()
    for num, (wtype, value) in sorted(fields.items()):
        if isinstance(value, list):
            for v in value: result.extend(encode_field(num, wtype, v))
        else:
            result.extend(encode_field(num, wtype, value))
    return bytes(result)

if __name__ == "__main__":
    msg = {1: (LEN, "hello"), 2: (VARINT, 42), 3: (VARINT, 100)}
    enc = encode_message(msg)
    print(f"Encoded: {enc.hex()} ({len(enc)} bytes)")
    dec = decode_message(enc)
    print(f"Decoded: {dec}")
