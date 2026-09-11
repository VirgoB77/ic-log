#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ページにぶら下がっている Excel を取ってきて、中身を確かめる。

大阪府と大阪市は、届出を表ではなく Excel で出している。
Excel は表がそのまま入っているので、HTMLを読むより正確で壊れにくい。

やること
  1. 保存ずみのページ（data/raw/）から Excel へのリンクを拾う
  2. まだ持っていないものだけ落として data/files/<id>/ に置く
  3. .xlsx は中身を開いて、シート名・行数・見出しを報告する

同じ版を毎日落とさない
  自治体はファイル名に日付を入れている（ju_20260818.xlsx など）ので、
  更新されると名前が変わる。名前で持っているかを見れば、版が変わったときだけ増える。

PDFは取らない
  兵庫県の資料は1本8MBあり、44本で350MBになる。置き場所が持たない。

.xls（古い形式）は落とすだけで中身は読まない
  中身がXMLではないので標準ライブラリでは開けない。読むには別のライブラリが要る。
"""

import glob
import html
import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
FILES = os.path.join(HERE, "data", "files")

UA = "shutten-recon/0.1 (+https://github.com/VirgoB77/ic-log)"
WAIT = 2
TIMEOUT = 90
MAX_BYTES = 20 * 1024 * 1024      # 1本がこれより大きければ見送る
PDF_MAX_BYTES = 2 * 1024 * 1024   # PDFはこれより大きければ見送る（資料の束を避ける）
WANT = re.compile(r"\.(xlsx|xls|csv)(\?|$)", re.I)
WANT_PDF = re.compile(r"\.pdf(\?|$)", re.I)

# PDFそのものが一覧になっている収集先だけ、PDFも落とす。
# 兵庫県のように「届出1件ごとの資料8MB」を並べているところは対象外。
# （sources.json の "pdf": true で指定する）

socket.setdefaulttimeout(TIMEOUT)

sys.path.insert(0, HERE)
import xlsx  # noqa: E402
import pdf as pdflib  # noqa: E402


def newest_raw(source):
    """そのソースの、いちばん新しい保存ページを返す。"""
    found = sorted(glob.glob(os.path.join(RAW, source, "*.html")))
    return found[-1] if found else None


def excel_links(path, base_url, want=WANT):
    """保存ページから Excel/CSV（や PDF）のリンクを拾う（重複は除く）。"""
    with open(path, encoding="utf-8", errors="replace") as f:
        page = f.read()
    out, seen = [], set()
    for m in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', page, re.S | re.I):
        href = html.unescape(m.group(1))
        if not want.search(href):
            continue
        url = urllib.parse.urljoin(base_url, href)
        if url in seen:
            continue
        seen.add(url)
        label = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(2))).strip()
        out.append((url, label[:60]))
    return out


def safe_name(url):
    """URL から、そのまま置けるファイル名を作る。"""
    name = os.path.basename(urllib.parse.urlparse(url).path) or "file"
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    return name[:100]


def download(url, dest, limit=MAX_BYTES):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ja"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        size = int(r.headers.get("Content-Length") or 0)
        if size > limit:
            raise ValueError(f"大きすぎる（{size:,}バイト）ので見送った")
        data = r.read(limit + 1)
    if len(data) > limit:
        raise ValueError("大きすぎるので見送った")
    with open(dest, "wb") as f:
        f.write(data)
    return len(data)


def peek(path):
    """中を開いて、行数と見出しを返す。.xlsx と .pdf に対応。"""
    if path.lower().endswith(".pdf"):
        try:
            rows = pdflib.extract_rows(path)
        except Exception as e:
            return {"error": f"{type(e).__name__}: {e}"}
        if not rows:
            return {"error": "文字が取れなかった（紙をスキャンしたPDFかもしれない）"}
        head = max(rows[:4], key=len) if rows else []
        return {"(PDF)": {"rows": len(rows), "header": [c[:20] for c in head[:8]]}}
    if not path.lower().endswith(".xlsx"):
        return None
    try:
        sheets = xlsx.read(path)
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
    out = {}
    for name, rows in sheets.items():
        head = next((r for r in rows if sum(1 for c in r if c) >= 2), [])
        out[name] = {"rows": len(rows), "header": [c[:20] for c in head[:8]]}
    return out


def main():
    with open(os.path.join(HERE, "sources.json"), encoding="utf-8") as f:
        sources = {s["id"]: s for s in json.load(f)["sources"]}

    wanted = sys.argv[1:] or [s for s, v in sources.items()
                              if s.startswith("osaka") or v.get("pdf")]
    lines = ["# Excelを取ってきた結果", ""]
    got = skipped = failed = 0

    for sid in wanted:
        src = sources.get(sid)
        if not src or not src.get("url"):
            continue
        raw = newest_raw(sid)
        if not raw:
            lines.append(f"### {src['name']}\n\n- まだページを保存していない\n")
            continue

        links = excel_links(raw, src["url"])
        kinds = ["Excel/CSV"]
        if src.get("pdf"):
            # 辿った先のページにもPDFが下がっているので、そこも見る
            for extra in sorted(glob.glob(os.path.join(RAW, sid, "*--*.html"))):
                links += excel_links(extra, src["url"], WANT_PDF)
            links += excel_links(raw, src["url"], WANT_PDF)
            seen_u = set()
            links = [(u, l) for u, l in links if not (u in seen_u or seen_u.add(u))]
            kinds.append("PDF")
        lines.append(f"### {src['name']}")
        lines.append("")
        lines.append(f"- {'/'.join(kinds)} のリンク: {len(links)} 本")

        d = os.path.join(FILES, sid)
        os.makedirs(d, exist_ok=True)

        for url, label in links:
            dest = os.path.join(d, safe_name(url))
            if os.path.exists(dest):
                skipped += 1
                continue
            try:
                n = download(url, dest,
                             PDF_MAX_BYTES if url.lower().endswith(".pdf") else MAX_BYTES)
            except (urllib.error.HTTPError, urllib.error.URLError, ValueError, OSError) as e:
                lines.append(f"  - 取れなかった {safe_name(url)} — {e}")
                failed += 1
                time.sleep(WAIT)
                continue
            got += 1
            lines.append(f"  - **{safe_name(url)}** {n:,}バイト … {label}")
            info = peek(dest)
            if info is None:
                lines.append("    - .xls は落としただけ（中を読むには別のライブラリが要る）")
            elif "error" in info:
                lines.append(f"    - 開けなかった: {info['error']}")
            else:
                for sheet, meta in info.items():
                    h = " | ".join(x for x in meta["header"] if x)
                    lines.append(f"    - シート「{sheet}」 {meta['rows']}行  {h}")
            time.sleep(WAIT)
        lines.append("")

    lines.insert(1, f"**新しく取れた {got}本 / すでに持っていた {skipped}本 / 取れなかった {failed}本**")
    text = "\n".join(lines)
    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    with open(os.path.join(HERE, "data", "files-report.md"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    gh = os.environ.get("GITHUB_STEP_SUMMARY")
    if gh:
        with open(gh, "a", encoding="utf-8") as f:
            f.write("\n" + text + "\n")


if __name__ == "__main__":
    main()
