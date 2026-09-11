#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""大店立地法の届出ページを偵察する。

いきなり全部を集めようとすると、たいてい最初のページで詰まる。
なので先に「そのページが機械で読める形かどうか」だけを確かめる。

やること
  1. robots.txt を見て、取りに行ってよいか確かめる
  2. ページを取得して data/raw/<id>/<日付>.html に残す
  3. 中身が「HTMLの表」か「PDFの並び」かを判定して、レポートに書く

判定の見方
  表        … HTMLの表がある。いちばん楽。すぐ自動化できる
  Excel     … xlsx/xls が置いてある。実はいちばん楽なこともある
  PDF       … PDFのリンクが並んでいる。中を読むのに一手間かかる
  わからない … 自分の目で見に行く必要がある

Python 3 の標準ライブラリだけで動く。GitHub Actions でそのまま動く。
"""

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
import urllib.robotparser
from datetime import date
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "shutten-recon/0.1 (+https://github.com/VirgoB77/ic-log)"
WAIT = 2          # 同じ相手に続けて出すときに空ける秒数。迷惑をかけない
TIMEOUT = 40

# robots.txt を読む urllib.robotparser はタイムアウトを指定できず、
# 既定のままだと相手が黙ったときに永久に待つ。ソケット側で縛っておく。
socket.setdefaulttimeout(TIMEOUT)


# ---------------------------------------------------------------- 文字コード

def decide_charset(raw, content_type):
    """Content-Type と meta タグから文字コードを決める。

    自治体のページは UTF-8 のことが多いが、古いものは Shift_JIS が残っている。
    """
    m = re.search(r"charset=([\w\-]+)", content_type or "", re.I)
    if m:
        return m.group(1)
    head = raw[:4096].decode("ascii", "ignore")
    m = re.search(r'charset=["\']?([\w\-]+)', head, re.I)
    if m:
        return m.group(1)
    return "utf-8"


def to_text(raw, content_type):
    cs = decide_charset(raw, content_type)
    for enc in (cs, "utf-8", "cp932", "euc_jp"):
        try:
            return raw.decode(enc), enc
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", "replace"), "utf-8(replace)"


# ---------------------------------------------------------------- HTML を読む

class Scanner(HTMLParser):
    """表とリンクだけを拾う。中身の意味までは見ない。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []          # 表ごとの {rows, cols, header}
        self.links = []           # (href, 文字列)
        self._tstack = []
        self._row_cells = 0
        self._cell_buf = None
        self._href = None
        self._atext = []

    # -- 表
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "table":
            self._tstack.append({"rows": 0, "cols": 0, "header": []})
        elif tag == "tr" and self._tstack:
            self._row_cells = 0
        elif tag in ("td", "th") and self._tstack:
            self._row_cells += 1
            self._cell_buf = []
        elif tag == "a":
            self._href = d.get("href")
            self._atext = []

    def handle_endtag(self, tag):
        if tag == "table" and self._tstack:
            self.tables.append(self._tstack.pop())
        elif tag == "tr" and self._tstack:
            t = self._tstack[-1]
            t["rows"] += 1
            t["cols"] = max(t["cols"], self._row_cells)
            if t["rows"] == 1:
                pass  # ヘッダは td/th の中身を集めた時点で入れてある
        elif tag in ("td", "th") and self._tstack and self._cell_buf is not None:
            t = self._tstack[-1]
            text = "".join(self._cell_buf).strip()
            if t["rows"] == 0 and len(t["header"]) < 12:
                t["header"].append(text[:24])
            self._cell_buf = None
        elif tag == "a" and self._href is not None:
            self.links.append((self._href, "".join(self._atext).strip()[:60]))
            self._href = None

    def handle_data(self, data):
        if self._cell_buf is not None:
            self._cell_buf.append(data)
        if self._href is not None:
            self._atext.append(data)


# ---------------------------------------------------------------- 取りに行く

def follow_links(page, base_url):
    """目次ページから、年度別ページなど「その先」のリンクを選ぶ。

    堺市や和泉市のように、入口は目次だけで、実物は1階層下にあることが多い。
    ここで拾わないと「表が無いページ」に見えてしまう。
    """
    out, seen = [], set()
    for m in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', page, re.S | re.I):
        label = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(2))).strip()
        if not label or len(label) > 60:
            continue
        if FOLLOW_SKIP.search(label):
            continue
        if not (FOLLOW_TEXT.search(label) and FOLLOW_TOPIC.search(label)):
            continue
        url = urllib.parse.urljoin(base_url, html.unescape(m.group(1)))
        if not url.startswith("http") or url in seen or url == base_url:
            continue
        # 同じサイトの中だけ辿る。よそへ出ていかない
        if urllib.parse.urlparse(url).netloc != urllib.parse.urlparse(base_url).netloc:
            continue
        seen.add(url)
        out.append((url, label))
    return out


def slug_of(url):
    """辿った先を保存するときのファイル名の一部。"""
    path = urllib.parse.urlparse(url).path
    name = re.sub(r"[^A-Za-z0-9._-]", "_", path.strip("/").replace("/", "-"))
    return (name or "page")[-60:]


def check_robots(url):
    """robots.txt で禁じられていないか確かめる。分からないときは True。"""
    p = urllib.parse.urlparse(url)
    robots = f"{p.scheme}://{p.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots)
    try:
        rp.read()
    except Exception:
        return True, "robots.txt が読めなかった（取得は続ける）"
    ok = rp.can_fetch(UA, url)
    return ok, ("許可" if ok else "robots.txt で拒否されている")


def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ja",
    })
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.status, r.headers.get("Content-Type", ""), r.read()


# ---------------------------------------------------------------- 判定する

KEYWORDS = ["新設", "変更", "廃止", "縦覧", "届出", "店舗面積", "開店"]

# 目次ページのリンク文字から、その先に一覧がありそうなものを選ぶ。
# 「令和N年度」だけを手がかりにすると、人権セミナーや中小企業支援の
# ページまで拾ってしまったので、届出か縦覧の語が入っていることを必須にする。
# 「届出」だけだと、アスベスト・騒音・水道・駐車場など市のあらゆる届出を
# 拾ってしまう（箕面市の窓口ページで実際に起きた）。
# 「届出か縦覧」であることに加えて、大規模小売店舗まわりの語が要る。
FOLLOW_TEXT = re.compile(r"届出|縦覧")
FOLLOW_TOPIC = re.compile(r"大規模|中規模|小売|大店|届出状況|縦覧状況|状況|第\s*\d+\s*条|年度")
# 様式のダウンロードや申請の入口に逃げないよう、明らかに違うものは弾く
FOLLOW_SKIP = re.compile(r"手引|様式|ワード|エクセル|\.doc|\.xls|要綱|申請書|"
                         r"お問い合わせ|電子申請|検索|一覧表示|ダウンロード")
FOLLOW_MAX = 12          # 1つの目次から辿る数の上限。相手に迷惑をかけないため


def analyze(text, base_url):
    s = Scanner()
    try:
        s.feed(text)
    except Exception as e:
        return {"error": f"HTMLの解析に失敗: {e}"}

    # 中身のある表だけを見る（2行2列以上）
    real = [t for t in s.tables if t["rows"] >= 2 and t["cols"] >= 2]
    real.sort(key=lambda t: t["rows"] * t["cols"], reverse=True)

    pdfs, excels = [], []
    for href, label in s.links:
        low = href.lower()
        full = urllib.parse.urljoin(base_url, href)
        if low.endswith(".pdf"):
            pdfs.append((full, label))
        elif low.endswith((".xlsx", ".xls", ".csv")):
            excels.append((full, label))

    found = [k for k in KEYWORDS if k in text]
    years = sorted(set(re.findall(r"(?:令和|平成)\s*\d{1,2}\s*年", text)))[:8]

    if real and real[0]["rows"] >= 3:
        verdict = "表"
    elif excels:
        verdict = "Excel"
    elif len(pdfs) >= 3:
        verdict = "PDF"
    else:
        verdict = "わからない"

    return {
        "verdict": verdict,
        "tables": len(real),
        "biggest": real[0] if real else None,
        "pdf_count": len(pdfs),
        "pdf_sample": pdfs[:5],
        "excel_count": len(excels),
        "excel_sample": excels[:5],
        "keywords": found,
        "years": years,
        "links_total": len(s.links),
    }


# ---------------------------------------------------------------- レポート

def report_one(src, res):
    out = []
    out.append(f"### {src['name']}")
    out.append("")
    out.append(f"- URL: {src['url']}")
    if src.get("note"):
        out.append(f"- メモ: {src['note']}")

    if res.get("skipped"):
        out.append(f"- **結果: 取りに行かなかった（{res['skipped']}）**")
        out.append("")
        return "\n".join(out)

    if res.get("fetch_error"):
        out.append(f"- **結果: 取得できなかった — {res['fetch_error']}**")
        out.append("")
        return "\n".join(out)

    out.append(f"- robots.txt: {res['robots']}")
    out.append(f"- HTTP {res['status']} / {res['encoding']} / {res['bytes']:,} バイト")

    a = res["analysis"]
    if a.get("error"):
        out.append(f"- **{a['error']}**")
        out.append("")
        return "\n".join(out)

    out.append(f"- **判定: {a['verdict']}**")
    out.append(f"- 表 {a['tables']} 個 / PDFリンク {a['pdf_count']} 本 / Excel {a['excel_count']} 本")

    if a["biggest"]:
        b = a["biggest"]
        out.append(f"- いちばん大きい表: {b['rows']} 行 × {b['cols']} 列")
        if b["header"]:
            out.append(f"  - 見出しらしき行: {' | '.join(x for x in b['header'] if x)}")
    for label, items in (("PDF", a["pdf_sample"]), ("Excel", a["excel_sample"])):
        for url, text in items:
            out.append(f"  - {label}: {text or '(名前なし)'} → {url}")

    if a["keywords"]:
        out.append(f"- 出てきた言葉: {' / '.join(a['keywords'])}")
    if a["years"]:
        out.append(f"- 年度らしき表記: {' / '.join(a['years'])}")

    if res.get("followed"):
        cap = res.get("follow_capped")
        note = f"（{cap[0]}本見つかったが上限{cap[1]}本まで）" if cap else ""
        out.append(f"- **この先を辿った: {len(res['followed'])}本** {note}")
        for label, a2, err in res["followed"]:
            if err:
                out.append(f"  - {label[:34]} … 取れなかった（{err}）")
            else:
                extra = f" {a2['biggest']['rows']}行×{a2['biggest']['cols']}列" if a2.get("biggest") else ""
                out.append(f"  - {label[:34]} … **{a2['verdict']}**{extra}")
    out.append("")
    return "\n".join(out)


def main():
    with open(os.path.join(HERE, "sources.json"), encoding="utf-8") as f:
        sources = json.load(f)["sources"]

    only = sys.argv[1] if len(sys.argv) > 1 else None
    today = date.today().isoformat()
    raw_dir = os.path.join(HERE, "data", "raw")

    lines = [
        f"# 大店立地法 届出ページ 偵察レポート（{today}）",
        "",
        "「そのページが機械で読める形か」だけを見ている。",
        "判定が **表** か **Excel** なら自動化しやすい。**PDF** なら一手間、",
        "**わからない** なら自分の目で見に行く必要がある。",
        "",
    ]

    counts = {}
    for src in sources:
        if only and only not in (src["id"], src.get("area", "")):
            continue
        res = {}

        if not src.get("enabled", True):
            res["skipped"] = src.get("note", "いまは対象外にしている")
            lines.append(report_one(src, res))
            continue

        ok, why = check_robots(src["url"])
        res["robots"] = why
        if not ok:
            res["skipped"] = why
            lines.append(report_one(src, res))
            counts["拒否"] = counts.get("拒否", 0) + 1
            continue

        try:
            status, ctype, raw = fetch(src["url"])
        except urllib.error.HTTPError as e:
            res["fetch_error"] = f"HTTP {e.code}"
            lines.append(report_one(src, res))
            counts["失敗"] = counts.get("失敗", 0) + 1
            time.sleep(WAIT)
            continue
        except Exception as e:
            res["fetch_error"] = f"{type(e).__name__}: {e}"
            lines.append(report_one(src, res))
            counts["失敗"] = counts.get("失敗", 0) + 1
            time.sleep(WAIT)
            continue

        text, enc = to_text(raw, ctype)
        res.update(status=status, encoding=enc, bytes=len(raw))
        res["analysis"] = analyze(text, src["url"])
        counts[res["analysis"]["verdict"]] = counts.get(res["analysis"]["verdict"], 0) + 1

        # 生のまま残す。これがアーカイブの最初の1枚になる
        d = os.path.join(raw_dir, src["id"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, f"{today}.html"), "wb") as f:
            f.write(raw)

        # 入口が目次だけのことが多い（堺市・和泉市・阪南市など）。
        # 表が無いページはその先を見に行く。
        if res["analysis"]["verdict"] == "わからない":
            cand = follow_links(text, src["url"])
            res["followed"] = []
            if len(cand) > FOLLOW_MAX:
                res["follow_capped"] = (len(cand), FOLLOW_MAX)
                cand = cand[:FOLLOW_MAX]
            for url2, label in cand:
                time.sleep(WAIT)
                try:
                    st2, ct2, raw2 = fetch(url2)
                except Exception as e:
                    res["followed"].append((label, None, f"{type(e).__name__}"))
                    continue
                t2, _ = to_text(raw2, ct2)
                a2 = analyze(t2, url2)
                with open(os.path.join(d, f"{today}--{slug_of(url2)}.html"), "wb") as f:
                    f.write(raw2)
                res["followed"].append((label, a2, None))
                counts[a2["verdict"]] = counts.get(a2["verdict"], 0) + 1

        lines.append(report_one(src, res))
        time.sleep(WAIT)

    summary = " / ".join(f"{k} {v}件" for k, v in sorted(counts.items())) or "対象なし"
    lines.insert(2, f"**まとめ: {summary}**")
    lines.insert(3, "")

    text = "\n".join(lines)
    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    with open(os.path.join(HERE, "data", "recon-report.md"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)

    # GitHub Actions の画面にも出す
    gh = os.environ.get("GITHUB_STEP_SUMMARY")
    if gh:
        with open(gh, "a", encoding="utf-8") as f:
            f.write(text)


if __name__ == "__main__":
    main()
