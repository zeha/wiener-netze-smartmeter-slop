"""Python mirror of the wiener_netze frame logic, checked against a test vector.

No captured telegram from a real meter is published in either reference
repository, so this test builds a synthetic frame: a plaintext with known
values is encrypted with AES-128-GCM (the meter's cipher, via pycryptodome),
wrapped into a 105-byte frame with a CRC-16/X-25 FCS, and then decoded with
exactly the steps the C++ component uses (CRC check, AES-CTR with IV
system title + frame counter + 00 00 00 02, fixed offsets).

When you have a real capture, put it in test/vectors.json (see README.md);
it is then checked as well.

Run: .venv/bin/python test/decrypt_test.py
"""

import json
from datetime import datetime
from pathlib import Path
import sys

from Crypto.Cipher import AES

FRAME_LENGTH = 105
HEADER_LENGTH = 14
PAYLOAD_LENGTH = FRAME_LENGTH - HEADER_LENGTH - 17  # 74


def crc16_x25(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0x8408 if crc & 1 else crc >> 1
    return crc ^ 0xFFFF


def decode(frame: bytes, key: bytes) -> dict:
    """Same steps as WienerNetze::handle_frame_() in wiener_netze.cpp."""
    assert len(frame) == FRAME_LENGTH and frame[0:2] == b"\x7e\xa0"
    crc = crc16_x25(frame[1 : FRAME_LENGTH - 3])
    expected = frame[FRAME_LENGTH - 2] * 256 + frame[FRAME_LENGTH - 3]
    if crc != expected:
        raise ValueError(f"CRC mismatch {crc:04X} != {expected:04X}")
    iv = (
        frame[HEADER_LENGTH : HEADER_LENGTH + 8]
        + frame[HEADER_LENGTH + 10 : HEADER_LENGTH + 14]
        + b"\x00\x00\x00\x02"
    )
    ct = frame[HEADER_LENGTH + 14 : HEADER_LENGTH + 14 + PAYLOAD_LENGTH]
    plain = AES.new(key, AES.MODE_CTR, initial_value=iv, nonce=b"").decrypt(ct)
    p = PAYLOAD_LENGTH

    def be(offset: int, length: int) -> int:
        return int.from_bytes(plain[offset : offset + length], "big")

    values = [be(p - 39 + 5 * i, 4) for i in range(8)]
    return {
        "timestamp": datetime(
            be(p - 52, 2), plain[p - 50], plain[p - 49],
            plain[p - 47], plain[p - 46], plain[p - 45],
        ).strftime("%Y-%m-%d %H:%M:%S"),
        "energy_active_plus": values[0] / 1000,
        "energy_active_minus": values[1] / 1000,
        "energy_reactive_plus": values[2] / 1000,
        "energy_reactive_minus": values[3] / 1000,
        "power_active_plus": values[4],
        "power_active_minus": values[5],
        "power_reactive_plus": values[6],
        "power_reactive_minus": values[7],
    }


def build_synthetic_frame(key: bytes) -> bytes:
    plain = bytearray(PAYLOAD_LENGTH)
    p = PAYLOAD_LENGTH
    plain[p - 52 : p - 50] = (2026).to_bytes(2, "big")
    plain[p - 50 : p - 44] = bytes([11, 8, 0, 14, 30, 45])  # month, day, weekday, h, m, s
    for i, v in enumerate([1234567, 89012, 3456, 789, 1500, 0, 42, 7]):
        plain[p - 39 + 5 * i - 1] = 0x06  # DLMS tag double-long-unsigned
        plain[p - 39 + 5 * i : p - 35 + 5 * i] = v.to_bytes(4, "big")

    system_title = bytes.fromhex("49534b6912345678")  # "ISK" + serial (made up)
    frame_counter = bytes.fromhex("0001e240")
    cipher = AES.new(key, AES.MODE_GCM, nonce=system_title + frame_counter)
    ct = cipher.encrypt(bytes(plain))

    frame = bytearray(FRAME_LENGTH)
    frame[0:2] = b"\x7e\xa0"
    frame[2] = FRAME_LENGTH - 2  # HDLC length field
    frame[HEADER_LENGTH : HEADER_LENGTH + 8] = system_title
    frame[HEADER_LENGTH + 8] = 0x5F  # length octet (made up)
    frame[HEADER_LENGTH + 9] = 0x20  # security control: encryption only
    frame[HEADER_LENGTH + 10 : HEADER_LENGTH + 14] = frame_counter
    frame[HEADER_LENGTH + 14 : HEADER_LENGTH + 14 + PAYLOAD_LENGTH] = ct
    crc = crc16_x25(frame[1 : FRAME_LENGTH - 3])
    frame[FRAME_LENGTH - 3] = crc & 0xFF
    frame[FRAME_LENGTH - 2] = crc >> 8
    frame[FRAME_LENGTH - 1] = 0x7E
    return bytes(frame)


def main() -> int:
    # CRC-16/X-25 catalogue check value
    assert crc16_x25(b"123456789") == 0x906E

    key = bytes.fromhex("0123456789abcdef0123456789abcdef")  # placeholder, not a meter key
    frame = build_synthetic_frame(key)
    got = decode(frame, key)
    assert got == {
        "timestamp": "2026-11-08 14:30:45",
        "energy_active_plus": 1234.567,
        "energy_active_minus": 89.012,
        "energy_reactive_plus": 3.456,
        "energy_reactive_minus": 0.789,
        "power_active_plus": 1500,
        "power_active_minus": 0,
        "power_reactive_plus": 42,
        "power_reactive_minus": 7,
    }, got
    print("synthetic frame: OK", got)

    broken = bytearray(frame)
    broken[50] ^= 0x01
    try:
        decode(bytes(broken), key)
    except ValueError:
        print("corrupted frame rejected by CRC: OK")
    else:
        raise AssertionError("corrupted frame was accepted")

    vectors = Path(__file__).with_name("vectors.json")
    if vectors.exists():
        for vec in json.loads(vectors.read_text()):
            got = decode(bytes.fromhex(vec["frame"]), bytes.fromhex(vec["key"]))
            for name, value in vec["expected"].items():
                assert got[name] == value, (name, got[name], value)
            print(f"captured vector {vec.get('name', '?')}: OK")
    else:
        print("no test/vectors.json: no captured telegram checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
