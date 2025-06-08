#!/usr/bin/env python3
"""
Deduplicate password entries from CSV read on standard input.

Input CSV rows have the format:
    name,url,username,password,note

Rows are considered duplicates when both of these match:
  • The registered domain extracted from the URL (e.g. "example.com").
  • The username field.

The first occurrence of each (domain, username) pair is kept; later
duplicates are discarded. The original row order is otherwise preserved.

Usage:
    python3 merge_passwords.py < input.csv > output.csv

No files are modified on disk; everything happens via stdin/stdout.
Requires the third‑party library `tldextract`.
"""
import sys
import csv
from typing import Tuple
import tldextract

def registered_domain(url: str) -> str:
    """Return the registered domain (e.g. example.com) from a URL."""
    ext = tldextract.extract(url)
    if ext.domain and ext.suffix:
        return f"{ext.domain}.{ext.suffix}"
    # Fallback: tldextract.registered_domain handles edge cases
    return ext.registered_domain or url

def main() -> None:
    reader = csv.reader(sys.stdin)
    writer = csv.writer(sys.stdout, lineterminator="\n")

    seen: set[Tuple[str, str]] = set()  # (domain, username)

    for row in reader:
        # Ensure row has exactly 5 fields, padding if necessary
        if len(row) < 5:
            row += [""] * (5 - len(row))
        name, url, username, password, note = row[:5]

        domain = registered_domain(url).lower()
        key = (domain, username)

        if key in seen:
            continue  # skip duplicate

        seen.add(key)
        writer.writerow([name, url, username, password, note])

if __name__ == "__main__":
    main()
