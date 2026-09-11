#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""保存したページから、届出の1件1件を取り出す。

recon.py が残した data/raw/<id>/<日付>.html を読んで、
data/parsed/<id>/<日付>.json に書き出す。

取り出すもの
  条文       … 第5条第1項＝新設、第6条＝変更、など。種類の手がかりになる
  届出年月日
  店舗名称
  縦覧期間   … いつまで公開されるか。これを過ぎると元ページから消える
  資料        … PDFなどへのリンク

県ごとにページの作りが違うので、県ごとに読み方を書く。
いまは兵庫県と神戸市の2つ。増やすときは EXTRACTORS に足す。

Python 3 の標準ライブラリだけで動く。
"""

import glob
import hashlib
import html
import json
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xlsx import _serial_to_date as serial_to_date  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
OUT = os.path.join(HERE, "data", "parsed")


# ---------------------------------------------------------------- 下ごしらえ

def text_of(fragment):
    """タグを落として、ふつうの文字列にする。"""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def tables_with_context(page):
    """表を、その直前の見出しとセットで取り出す。

    兵庫県は「第6条第1項」という見出しの下に表を置いているので、
    見出しを覚えておかないと、新設なのか変更なのか分からなくなる。
    """
    out = []
    heading = ""
    pattern = r"<(h[1-4])\b[^>]*>(.*?)</\1>|<table\b(.*?)</table>"
    for m in re.finditer(pattern, page, re.S | re.I):
        if m.group(1):
            t = text_of(m.group(2))
            if t:
                heading = t
        else:
            out.append((heading, m.group(3)))
    return out


def rows_of(table_html, base_url):
    """表を「セルの文字列の並び」と「その行にあったリンク」に分ける。"""
    rows = []
    for tr in re.findall(r"<tr\b.*?</tr>", table_html, re.S | re.I):
        cells, links = [], []
        for c in re.findall(r"<t[dh]\b.*?</t[dh]>", tr, re.S | re.I):
            cells.append(text_of(c))
            for href in re.findall(r'href=["\']([^"\']+)["\']', c, re.I):
                links.append(urllib.parse.urljoin(base_url, html.unescape(href)))
        if any(cells):
            rows.append((cells, links))
    return rows


# ---------------------------------------------------------------- 日付を直す

ERA = {"令和": 2018, "平成": 1988, "昭和": 1925}


def to_iso(s):
    """「令和8年4月23日」も「2026年7月27日」も 2026-04-23 の形にする。"""
    if not s:
        return None
    s = s.replace("元年", "1年")
    m = re.search(r"(令和|平成|昭和)\s*(\d{1,2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", s)
    if m:
        y = ERA[m.group(1)] + int(m.group(2))
        return f"{y:04d}-{int(m.group(3)):02d}-{int(m.group(4)):02d}"
    m = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", s)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.search(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", s)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return None


def span_of(s):
    """「令和8年5月12日～ 令和8年9月14日」から始まりと終わりを取る。"""
    if not s:
        return None, None
    parts = re.split(r"～|~|から", s, maxsplit=1)
    a = to_iso(parts[0])
    b = to_iso(parts[1]) if len(parts) > 1 else None
    return a, b


def coerce_date_column(rows, threshold=0.6):
    """列ごとに「ここは日付の列」と判断して、はみ出したセルを揃える。

    役所のExcelは同じ列でも手打ちのブレがあり、日付書式のセルと、
    ただの数字（Excelの連番）と、「令和元年６月30日」という文字列が混ざる。

      グルメシティ瓢箪山店 | … | 43901      | 43916
      ブリスモール瓢箪山店 | … | 44251      | 令和元年６月30日
      イオン東大阪店      | … | 2021-04-27 | 2021-03-31

    その列の中身の多くが日付なら、残りも日付として読み直す。
    多くが日付でない列（店舗面積など）は数字のまま触らない。
    """
    if not rows:
        return rows
    width = max(len(r) for r in rows)
    out = [list(r) + [""] * (width - len(r)) for r in rows]

    for col in range(width):
        vals = [(i, out[i][col]) for i in range(len(out)) if out[i][col]]
        if len(vals) < 3:
            continue
        already = sum(1 for _, v in vals if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v))
        if already / len(vals) < threshold:
            continue                      # 日付の列ではない
        for i, v in vals:
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
                continue
            fixed = to_iso(v)             # 「令和元年６月30日」など
            if not fixed and re.fullmatch(r"\d{5}(\.\d+)?", v):
                fixed = serial_to_date(v)  # Excelの連番のまま残ったもの
            if fixed:
                out[i][col] = fixed
    return out


# ---------------------------------------------------------------- 見分ける

# 条文と、それが何の届出かの対応。
#
# 先頭から見ることが大事。「第6条第2項（附則第5条第1項）」のような書き方があり、
# 途中の「第5条」を拾うと変更を新設と読み違える。
#
#   第5条第1項  … 新設。新しい大型店ができる
#   第6条第5項  … 廃止。店舗面積が1000平米以下になる＝大型店でなくなる
#   第6条その他 … 変更。面積・営業時間・駐車場などの変更
#   第11条第3項 … 承継。設置者（建物の持ち主）が変わった
ARTICLE_MEANS = [
    (r"^法?\s*第\s*6\s*条\s*第\s*5\s*項", "廃止"),
    (r"^法?\s*第\s*5\s*条", "新設"),
    (r"^法?\s*第\s*6\s*条", "変更"),
    (r"^法?\s*第\s*8\s*条", "意見・勧告"),
    (r"^法?\s*第\s*11\s*条", "承継"),
]

# 届出ではない表（意見書など）はここで弾く
NOT_A_NOTICE = re.compile(r"意見書|市の意見|県の意見|公表")


def means_of(article):
    article = article.strip()
    for pat, name in ARTICLE_MEANS:
        if re.search(pat, article):
            return name
    return "不明"


def guess_columns(header):
    """見出し行から、どの列が何かを当てる。県ごとに列の順が違うため。"""
    idx = {}
    for i, h in enumerate(header):
        if re.search(r"届出.*(年月日|日)|受理", h):
            idx.setdefault("date", i)
        elif re.search(r"店舗名|名称", h):
            idx.setdefault("store", i)
        elif re.search(r"縦覧", h):
            idx.setdefault("span", i)
        elif re.search(r"概要|届出概要|資料", h):
            idx.setdefault("docs", i)
    return idx


# ---------------------------------------------------------------- 読み取る

def extract_generic(page, base_url, article_from):
    """兵庫県・神戸市に共通の読み方。

    article_from が "heading" なら直前の見出しから条文を取り、
    "firstrow" なら表の1行目の最初のセルから取る（神戸市がこの形）。
    """
    found = []
    for heading, table in tables_with_context(page):
        rows = rows_of(table, base_url)
        if len(rows) < 2:
            continue

        if article_from == "firstrow":
            article = rows[0][0][0] if rows[0][0] else ""
            rows = rows[1:]
        else:
            article = heading

        if not article or NOT_A_NOTICE.search(article):
            continue

        if not rows:
            continue
        header = rows[0][0]
        idx = guess_columns(header)
        if "store" not in idx or "date" not in idx:
            continue

        for cells, links in rows[1:]:
            def cell(k):
                i = idx.get(k)
                return cells[i] if i is not None and i < len(cells) else ""

            store = cell("store")
            if not store:
                continue
            d = to_iso(cell("date"))
            a, b = span_of(cell("span"))
            found.append({
                "article": article,
                "kind": means_of(article),
                "notified_on": d,
                "notified_raw": cell("date"),
                "store": store,
                "review_from": a,
                "review_to": b,
                "docs": [u for u in links if re.search(r"\.(pdf|xlsx?|docx?)$", u, re.I)],
            })
    return found


EXTRACTORS = {
    "hyogo-pref-juran": dict(
        base="https://web.pref.hyogo.lg.jp/ks21/wd24_000000018.html",
        how="heading"),
    "kobe-city": dict(
        base="https://www.city.kobe.lg.jp/a31812/business/sangyoshinko/shokogyo/koritenporitchi/daitenhp/index.html",
        how="firstrow"),
}


def make_key(source, rec):
    """同じ届出を日をまたいで同じものと見なすための目印。

    これがあるから「今日から消えた＝縦覧が終わった」が分かる。
    店舗名と届出日が変わらないかぎり同じ目印になる。
    """
    seed = f"{source}|{rec['article']}|{rec['notified_on']}|{rec['store']}"
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]


def parse_file(source, path):
    conf = EXTRACTORS[source]
    with open(path, encoding="utf-8", errors="replace") as f:
        page = f.read()
    recs = extract_generic(page, conf["base"], conf["how"])
    for r in recs:
        r["source"] = source
        r["key"] = make_key(source, r)
    return recs


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    total = 0
    summary = []

    for source in sorted(EXTRACTORS):
        if only and only != source:
            continue
        for path in sorted(glob.glob(os.path.join(RAW, source, "*.html"))):
            day = os.path.splitext(os.path.basename(path))[0]
            recs = parse_file(source, path)
            d = os.path.join(OUT, source)
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, f"{day}.json"), "w", encoding="utf-8") as f:
                json.dump(recs, f, ensure_ascii=False, indent=1)
            kinds = {}
            for r in recs:
                kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
            summary.append((source, day, len(recs), kinds))
            total += len(recs)

    print(f"# 取り出した結果（合計 {total} 件）\n")
    for source, day, n, kinds in summary:
        k = " / ".join(f"{a} {b}件" for a, b in sorted(kinds.items()))
        print(f"- {source} {day}: **{n}件**（{k}）")

    gh = os.environ.get("GITHUB_STEP_SUMMARY")
    if gh:
        with open(gh, "a", encoding="utf-8") as f:
            f.write(f"\n## 取り出し結果: 合計 {total} 件\n")
            for source, day, n, kinds in summary:
                f.write(f"- {source} {day}: {n}件\n")


if __name__ == "__main__":
    main()
