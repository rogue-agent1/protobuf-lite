from protobuf_lite import encode_message, decode_message, encode_varint, decode_varint, VARINT, LEN
v = encode_varint(300)
assert decode_varint(v)[0] == 300
msg = {1: (LEN, "hello"), 2: (VARINT, 42)}
enc = encode_message(msg)
dec = decode_message(enc)
assert dec[1] == "hello"
assert dec[2] == 42
print("Protobuf tests passed")