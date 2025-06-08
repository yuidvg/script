#!/usr/bin/env python3
"""
target.csv から reference.csv と
  ・ドメイン（サブドメイン／パス無視）
  ・Username
  ・Password
が一致する行を除外して標準出力へ書き出すスクリプト
"""

import csv
import re
import sys
import urllib.parse


def extract_domain(url: str) -> str:
    """URL から登録ドメインだけを取り出す（www 等は除外）。"""
    # 「example.com (memo)」のような余計な部分を削る
    url = re.split(r'\s|\(', url.strip(), 1)[0]

    # スキームが無い場合は付与してパース
    if not re.match(r'^[a-zA-Z][\w+.-]*://', url):
        url_to_parse = "http://" + url
    else:
        url_to_parse = url

    host = urllib.parse.urlparse(url_to_parse).hostname or url

    # 先頭 www. を除去
    host = re.sub(r"^www\.", "", host, flags=re.I)

    #―― tldextract が入っている場合はより正確に ――#
    try:
        import tldextract  # 標準環境に無ければ except へ
        ext = tldextract.extract(host)
        registered = ".".join(
            part for part in (ext.domain, ext.suffix) if part
        )
        if registered:
            return registered.lower()
    except ImportError:
        pass  # フォールバックへ

    #―― フォールバック: ホスト末尾 2 ラベルを取得 ――#
    parts = host.split(".")
    return ".".join(parts[-2:]).lower() if len(parts) >= 2 else host.lower()


def build_reference_set(ref_path: str) -> set[tuple[str, str, str]]:
    """(domain, username, password) の集合を作る。"""
    ref_set: set[tuple[str, str, str]] = set()

    with open(ref_path, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) < 4:
                continue
            domain = extract_domain(row[1])      # URL (memo)
            username = row[2]                    # Username
            password = row[3]                    # Password
            ref_set.add((domain, username, password))

    return ref_set


def stream_filtered_target(tgt_path: str, ref_set: set[tuple[str, str, str]]):
    """target 行を読み込み、重複が無ければそのまま stdout へ。"""
    writer = csv.writer(sys.stdout, lineterminator="\n")
    with open(tgt_path, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) < 4:
                continue
            domain = extract_domain(row[1])      # url
            username = row[2]                    # username
            password = row[3]                    # password
            if (domain, username, password) not in ref_set:
                writer.writerow(row)


def main():
    if len(sys.argv) != 3:
        sys.exit(f"Usage: {sys.argv[0]} target.csv reference.csv")

    target_path, ref_path = sys.argv[1], sys.argv[2]
    ref_set = build_reference_set(ref_path)
    stream_filtered_target(target_path, ref_set)


if __name__ == "__main__":
    main()