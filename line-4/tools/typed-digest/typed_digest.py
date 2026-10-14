#!/usr/bin/env python3
"""Offline EIP-712 digest calculator. No wallet, signing, or network code."""

import argparse
import json
import re
import sys
from pathlib import Path

MASK = (1 << 64) - 1
RATE = 136  # bytes for Keccak-256
ROT = (
    (0, 36, 3, 41, 18),
    (1, 44, 10, 45, 2),
    (62, 6, 43, 15, 61),
    (28, 55, 25, 21, 56),
    (27, 20, 39, 8, 14),
)
RC = (
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A,
    0x8000000080008000, 0x000000000000808B, 0x0000000080000001,
    0x8000000080008081, 0x8000000000008009, 0x000000000000008A,
    0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089,
    0x8000000000008003, 0x8000000000008002, 0x8000000000000080,
    0x000000000000800A, 0x800000008000000A, 0x8000000080008081,
    0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
)
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
ARRAY = re.compile(r"^(.*)\[([0-9]*)\]$")
INTEGER = re.compile(r"^(u?int)([0-9]+)$")
FIXED_BYTES = re.compile(r"^bytes([0-9]+)$")
DECIMAL = re.compile(r"^-?(0|[1-9][0-9]*)$")
HEX = re.compile(r"^0[xX][0-9a-fA-F]+$")
BUILTIN = {"address", "bool", "bytes", "string"}


class TypedDataError(ValueError):
    pass


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise TypedDataError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def rot64(value, n):
    return ((value << n) | (value >> (64 - n))) & MASK if n else value


def keccak_f(state):
    for rc in RC:
        columns = [state[x] ^ state[x + 5] ^ state[x + 10] ^ state[x + 15] ^ state[x + 20] for x in range(5)]
        for x in range(5):
            delta = columns[(x - 1) % 5] ^ rot64(columns[(x + 1) % 5], 1)
            for y in range(5):
                state[x + 5 * y] ^= delta
        shifted = [0] * 25
        for x in range(5):
            for y in range(5):
                shifted[y + 5 * ((2 * x + 3 * y) % 5)] = rot64(state[x + 5 * y], ROT[x][y])
        for y in range(5):
            for x in range(5):
                state[x + 5 * y] = shifted[x + 5 * y] ^ ((~shifted[(x + 1) % 5 + 5 * y]) & shifted[(x + 2) % 5 + 5 * y])
                state[x + 5 * y] &= MASK
        state[0] ^= rc


def keccak256(data):
    """Ethereum Keccak-256, with Keccak padding (not NIST SHA3-256)."""
    state = [0] * 25
    padded = bytearray(data)
    padded.append(0x01)
    padded.extend(b"\0" * ((RATE - len(padded) % RATE) % RATE))
    padded[-1] ^= 0x80
    for start in range(0, len(padded), RATE):
        block = padded[start:start + RATE]
        for offset in range(0, RATE, 8):
            state[offset // 8] ^= int.from_bytes(block[offset:offset + 8], "little")
        keccak_f(state)
    return b"".join(state[i].to_bytes(8, "little") for i in range(4))


def parse_hex(value, length=None):
    if not isinstance(value, str) or not value.startswith("0x") or len(value) % 2 or not re.fullmatch(r"0x[0-9a-fA-F]*", value):
        raise TypedDataError("expected an even-length 0x-prefixed hex string")
    raw = bytes.fromhex(value[2:])
    if length is not None and len(raw) != length:
        raise TypedDataError(f"expected {length} bytes, got {len(raw)}")
    return raw


def parse_integer(value):
    if type(value) is int:
        return value
    if isinstance(value, str) and (DECIMAL.fullmatch(value) or HEX.fullmatch(value)):
        return int(value, 16 if value.lower().startswith("0x") else 10)
    raise TypedDataError("expected an integer or decimal/0x string")


def base_type(type_name):
    while True:
        match = ARRAY.fullmatch(type_name)
        if not match:
            return type_name
        if match.group(2) and (match.group(2).startswith("0") or int(match.group(2)) == 0):
            raise TypedDataError("fixed arrays need a positive canonical length")
        type_name = match.group(1)


def valid_type(type_name, types):
    base = base_type(type_name)
    if base in types or base in BUILTIN:
        return True
    match = INTEGER.fullmatch(base)
    if match:
        width = int(match.group(2))
        return str(width) == match.group(2) and width in range(8, 257, 8)
    match = FIXED_BYTES.fullmatch(base)
    return bool(match and str(int(match.group(1))) == match.group(1) and 1 <= int(match.group(1)) <= 32)


class Encoder:
    def __init__(self, types):
        if not isinstance(types, dict) or "EIP712Domain" not in types:
            raise TypedDataError("types must define EIP712Domain")
        self.types = types
        for struct, fields in types.items():
            if not isinstance(struct, str) or not IDENT.fullmatch(struct) or not isinstance(fields, list):
                raise TypedDataError("invalid struct declaration")
            if struct in BUILTIN or INTEGER.fullmatch(struct) or FIXED_BYTES.fullmatch(struct):
                raise TypedDataError(f"struct name {struct!r} conflicts with a built-in type")
            names = set()
            for field in fields:
                if not isinstance(field, dict) or set(field) != {"name", "type"}:
                    raise TypedDataError(f"invalid field in {struct}")
                name, type_name = field["name"], field["type"]
                if not isinstance(name, str) or not IDENT.fullmatch(name) or name in names:
                    raise TypedDataError(f"invalid or duplicate field in {struct}")
                if not isinstance(type_name, str) or not valid_type(type_name, types):
                    raise TypedDataError(f"unsupported type {type_name!r} in {struct}.{name}")
                names.add(name)

    def type_encoding(self, primary):
        if primary not in self.types:
            raise TypedDataError(f"unknown struct {primary!r}")
        seen = set()

        def visit(struct):
            for field in self.types[struct]:
                dependency = base_type(field["type"])
                if dependency in self.types and dependency != primary and dependency not in seen:
                    seen.add(dependency)
                    visit(dependency)

        visit(primary)

        def declaration(struct):
            fields = ",".join(f'{field["type"]} {field["name"]}' for field in self.types[struct])
            return f"{struct}({fields})"

        return declaration(primary) + "".join(declaration(name) for name in sorted(seen))

    def struct_hash(self, struct, value):
        if not isinstance(value, dict):
            raise TypedDataError(f"{struct} value must be an object")
        fields = self.types[struct]
        wanted = {field["name"] for field in fields}
        if set(value) != wanted:
            raise TypedDataError(f"{struct} fields differ: missing {sorted(wanted - set(value))}, extra {sorted(set(value) - wanted)}")
        encoded = keccak256(self.type_encoding(struct).encode("utf-8"))
        for field in fields:
            try:
                encoded += self.value_word(field["type"], value[field["name"]])
            except TypedDataError as exc:
                raise TypedDataError(f"{struct}.{field['name']}: {exc}") from exc
        return keccak256(encoded)

    def value_word(self, type_name, value):
        array = ARRAY.fullmatch(type_name)
        if array:
            inner, length = array.groups()
            if not isinstance(value, list):
                raise TypedDataError("array value must be a list")
            if length and len(value) != int(length):
                raise TypedDataError(f"array must have {length} elements")
            return keccak256(b"".join(self.value_word(inner, item) for item in value))
        if type_name in self.types:
            return self.struct_hash(type_name, value)
        if type_name == "string":
            if not isinstance(value, str):
                raise TypedDataError("string value required")
            return keccak256(value.encode("utf-8"))
        if type_name == "bytes":
            return keccak256(parse_hex(value))
        if type_name == "address":
            return parse_hex(value, 20).rjust(32, b"\0")
        if type_name == "bool":
            if type(value) is not bool:
                raise TypedDataError("boolean value required")
            return int(value).to_bytes(32, "big")
        match = FIXED_BYTES.fullmatch(type_name)
        if match:
            return parse_hex(value, int(match.group(1))).ljust(32, b"\0")
        match = INTEGER.fullmatch(type_name)
        if match:
            integer = parse_integer(value)
            width = int(match.group(2))
            signed = match.group(1) == "int"
            lower = -(1 << (width - 1)) if signed else 0
            upper = (1 << (width - 1)) - 1 if signed else (1 << width) - 1
            if not lower <= integer <= upper:
                raise TypedDataError(f"integer out of range for {type_name}")
            return (integer % (1 << 256)).to_bytes(32, "big")
        raise TypedDataError(f"unsupported type {type_name!r}")


def digest(typed_data):
    if not isinstance(typed_data, dict) or not {"types", "primaryType", "domain", "message"} <= set(typed_data):
        raise TypedDataError("input needs types, primaryType, domain, and message")
    if set(typed_data) != {"types", "primaryType", "domain", "message"}:
        raise TypedDataError("unexpected top-level typed-data fields")
    encoder = Encoder(typed_data["types"])
    primary = typed_data["primaryType"]
    if not isinstance(primary, str) or primary == "EIP712Domain" or primary not in encoder.types:
        raise TypedDataError("primaryType must name a message struct")
    domain = encoder.struct_hash("EIP712Domain", typed_data["domain"])
    message = encoder.struct_hash(primary, typed_data["message"])
    result = keccak256(b"\x19\x01" + domain + message)
    return {
        "primaryType": primary,
        "typeEncoding": encoder.type_encoding(primary),
        "domainSeparator": "0x" + domain.hex(),
        "messageHash": "0x" + message.hex(),
        "digest": "0x" + result.hex(),
    }


def main():
    parser = argparse.ArgumentParser(description="Calculate an EIP-712 digest offline; never signs")
    parser.add_argument("input", type=Path, help="typed-data JSON file")
    parser.add_argument("--expect", help="32-byte 0x digest to compare")
    args = parser.parse_args()
    try:
        with args.input.open(encoding="utf-8") as source:
            data = json.load(source, object_pairs_hook=unique_object)
        result = digest(data)
        if args.expect is not None:
            expected = parse_hex(args.expect, 32)
            result["matchesExpected"] = expected.hex() == result["digest"][2:]
        print(json.dumps(result, indent=2))
        return 0 if result.get("matchesExpected", True) else 1
    except (TypedDataError, ValueError, OSError) as exc:
        print(f"typed-digest: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
