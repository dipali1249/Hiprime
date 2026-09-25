#!/usr/bin/env python3
"""
Continuous large-prime search.

Tests odd numbers one by one with the Miller-Rabin primality test,
records every prime it finds, and saves progress so the next run
(automatically triggered by GitHub Actions) continues exactly where
this one stopped.

Usage:
    python prime_finder.py --hours 5.9
    python prime_finder.py --digits 200 --hours 0.5
    python prime_finder.py --start 10**60 --hours 1
"""

import argparse
import json
import os
import random
import signal
import time
from datetime import datetime, timezone

PROGRESS_FILE = "progress.json"
PRIMES_FILE = "primes.txt"
LOG_FILE = "search.log"
SAVE_INTERVAL = 30          # seconds between progress saves
DEFAULT_DIGITS = 100        # default size of numbers to search

_SMALL_PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]


def miller_rabin(n: int, rounds: int = 40) -> bool:
    """Probabilistic Miller-Rabin primality test.

    With 40 rounds the chance of a composite passing is below 2^-80,
    which is fine for record-keeping purposes.
    """
    if n < 2:
        return False
    for p in _SMALL_PRIMES:
        if n % p == 0:
            return n == p
    # write n-1 as d * 2^r with d odd
    d = n - 1
    r = 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for _ in range(rounds):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False  # composite
    return True


def parse_start(text: str) -> int:
    """Accept plain integers and expressions like 10**60."""
    text = text.replace(" ", "")
    if "**" in text:
        base, exp = text.split("**", 1)
        return int(base) ** int(exp)
    return int(text)


class PrimeSearch:
    def __init__(self, candidate: int, digits: int):
        self.candidate = candidate if candidate % 2 == 1 else candidate + 1
        self.digits = digits
        self.found = 0
        self.tested = 0
        self.stop_requested = False
        signal.signal(signal.SIGTERM, self._handle_stop)
        signal.signal(signal.SIGINT, self._handle_stop)

    def _handle_stop(self, signum, frame):
        self.stop_requested = True

    def save(self):
        state = {
            "candidate": self.candidate,
            "found": self.found,
            "tested": self.tested,
            "digits": self.digits,
            "updated_utc": datetime.now(timezone.utc).isoformat(),
        }
        tmp = PROGRESS_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, PROGRESS_FILE)

    def record_prime(self, p: int):
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        with open(PRIMES_FILE, "a") as f:
            f.write(f"{p}\n")
        with open(LOG_FILE, "a") as f:
            f.write(f"[{stamp}] prime #{self.found} found "
                    f"after testing {self.tested} candidates\n")
        print(f"  *** PRIME #{self.found} ***  ({len(str(p))} digits)")

    def run(self, hours: float):
        deadline = time.monotonic() + hours * 3600
        start = time.monotonic()
        last_save = start
        print(f"Searching for {self.digits}-digit primes for {hours} hours.")
        while not self.stop_requested and time.monotonic() < deadline:
            self.tested += 1
            if miller_rabin(self.candidate):
                self.found += 1
                self.record_prime(self.candidate)
            self.candidate += 2
            now = time.monotonic()
            if now - last_save >= SAVE_INTERVAL:
                self.save()
                last_save = now
                elapsed = now - start
                rate = self.tested / elapsed if elapsed > 0 else 0
                print(f"  progress: tested {self.tested}, found {self.found}, "
                      f"rate {rate:.1f} candidates/s")
        self.save()
        elapsed = (time.monotonic() - start) / 60
        reason = "stop signal" if self.stop_requested else "time limit"
        print(f"Stopped ({reason}) after {elapsed:.1f} minutes. "
              f"Tested {self.tested} candidates, found {self.found} primes.")
        print(f"Next run resumes from {self.candidate}.")


def main():
    parser = argparse.ArgumentParser(description="Continuous large-prime search")
    parser.add_argument("--hours", type=float, default=1.0,
                        help="length of this session in hours (default 1)")
    parser.add_argument("--digits", type=int, default=DEFAULT_DIGITS,
                        help="digit count for a fresh search (default 100)")
    parser.add_argument("--start", type=str, default=None,
                        help="start number for a fresh search, "
                             "e.g. 123456789 or 10**60")
    args = parser.parse_args()

    random.seed()

    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            state = json.load(f)
        search = PrimeSearch(int(state["candidate"]),
                             len(str(int(state["candidate"]))))
        search.found = int(state.get("found", 0))
        search.tested = int(state.get("tested", 0))
        print(f"Resuming from saved progress at {search.candidate}.")
    else:
        start_val = parse_start(args.start) if args.start else 10 ** (args.digits - 1)
        search = PrimeSearch(int(start_val), len(str(int(start_val))))
        print(f"Fresh search starting at {search.candidate}.")

    search.run(args.hours)


if __name__ == "__main__":
    main()
