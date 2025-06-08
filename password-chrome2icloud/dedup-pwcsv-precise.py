#!/usr/bin/env python3
"""
dedup_pwcsv_tld.py  —  Remove rows from target CSV that also appear in reference CSV,
matching on (registrable‑domain, username, password).

usage:
    python dedup_pwcsv_tld.py target.csv reference.csv > cleaned_target.csv
"""

import argparse
import csv
import re
import sys
from urllib.parse import urlsplit

import tldextract   # pip install tldextract


# ----------------------------------------------------------------------
def extract_domain(raw_url: str) -> str:
    """
    文字列から登録可能ドメイン (registrable domain) を小文字で返す。

    * target 側: "https://www.example.com/aaa"          -> example.com
    * reference 側: "example.com (memo)"               -> example.com
    * サブドメイン・パス・ポート・クエリはすべて無視
    """
    # "(memo)" や空白以降は無視
    url_part = re.split(r"\s|\(", raw_url.strip(), 1)[0]

    # スキームが無いと urlsplit が誤判定するので仮付け
    if "://" not in url_part:
        url_part = "https://" + url_part

    host = urlsplit(url_part).hostname or ""
    ext = tldextract.extract(host)
    # ext.domain と ext.suffix のどちらかが空になることがあるため、空要素は除外
    registrable = ".".join(part for part in (ext.domain, ext.suffix) if part)
    return registrable.lower()


# ----------------------------------------------------------------------
def build_reference_set(ref_path: str) -> set[tuple[str, str, str]]:
    """reference.csv から (domain, username, password) のセットを作る"""
    triples: set[tuple[str, str, str]] = set()
    with open(ref_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            domain = extract_domain(row.get("URL (memo)", ""))
            triples.add((domain, row.get("Username", ""), row.get("Password", "")))
    return triples


def filter_target(target_path: str, ref_set: set[tuple[str, str, str]]) -> None:
    """target.csv を読み込み、ref_set に無い行だけ stdout へ書く"""
    with open(target_path, newline="", encoding="utf-8") as f_in:
        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(sys.stdout, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            domain = extract_domain(row["url"])
            key = (domain, row["username"], row["password"])
            if key not in ref_set:
                writer.writerow(row)


# ----------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(
        description="Remove rows from target CSV already present in reference CSV"
    )
    ap.add_argument("target", help="target CSV (name,url,username,password,note)")
    ap.add_argument(
        "reference", help='reference CSV (Title, "URL (memo)",Username,Password,Notes,OTPAuth)'
    )
    args = ap.parse_args()

    ref_set = build_reference_set(args.reference)
    filter_target(args.target, ref_set)


if __name__ == "__main__":
    main()