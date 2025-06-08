#!/usr/bin/env python3
"""
dedup_pwcsv.py  --  remove rows from target CSV that exist in reference CSV
usage:
    python dedup_pwcsv.py target.csv reference.csv > cleaned_target.csv
"""

import argparse, csv, re, sys
from urllib.parse import urlsplit

# ------------------------------------------------------------
# 低依存でドメインを抽出する関数
# ------------------------------------------------------------
def extract_domain(raw_url: str) -> str:
    """
    Returns registrable domain part of a URL-like string.
    1. "example.com (memo)" -> example.com
    2. "https://www.sub.example.co.uk/aaa" -> example.co.uk
    3. "ftp://example.com"  -> example.com
    4. "example.com"        -> example.com
    ※ 正確を期すなら `pip install tldextract` して
       `return tldextract.extract(clean)[1:]` のように書き換えてください。
    """
    # 1) 余分なコメント "(memo)" など以降を切り捨て
    clean = re.split(r"\s|\(", raw_url.strip(), 1)[0]

    # スキームが無い場合は仮に https:// を付けてパース
    if "://" not in clean:
        clean = "https://" + clean

    host = urlsplit(clean).hostname or ""
    host = host.lstrip("www.")  # www. を無視

    parts = host.split(".")
    if len(parts) >= 2:
        domain = ".".join(parts[-2:])          # 例: example.com, co.jp
        # co.uk / co.jp のような second‑level TLD は簡易判定
        if domain in {"co.uk", "co.jp", "com.au", "co.nz"} and len(parts) >= 3:
            domain = ".".join(parts[-3:])
    else:
        domain = host
    return domain.lower()

# ------------------------------------------------------------
def build_reference_set(ref_path: str) -> set[tuple[str, str, str]]:
    """(domain, username, password) の set を作る"""
    triples = set()
    with open(ref_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dom = extract_domain(row.get("URL (memo)", ""))
            triples.add((dom, row.get("Username", ""), row.get("Password", "")))
    return triples

def filter_target(target_path: str, ref_set: set[tuple[str,str,str]]) -> None:
    """target を読み込み、ref_set に無い行だけ stdout へ書き出す"""
    with open(target_path, newline="", encoding="utf-8") as f_in:
        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(sys.stdout, fieldnames=reader.fieldnames)
        writer.writeheader()                     # ヘッダー行
        for row in reader:
            dom = extract_domain(row["url"])
            key = (dom, row["username"], row["password"])
            if key not in ref_set:
                writer.writerow(row)

# ------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(
        description="remove rows from target CSV already present in reference CSV"
    )
    ap.add_argument("target", help="target CSV (name,url,username,password,note)")
    ap.add_argument("reference", help='reference CSV (Title, "URL (memo)",Username,Password,...)')
    args = ap.parse_args()

    ref_set = build_reference_set(args.reference)
    filter_target(args.target, ref_set)

if __name__ == "__main__":
    main()