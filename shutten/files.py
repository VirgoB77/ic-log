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
import http.cookiejar

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
FILES = os.path.join(HERE, "data", "files")

UA = "shutten-recon/0.1 (+https://github.com/VirgoB77/ic-log)"
WAIT = 2
TIMEOUT = 90
PDF_TIMEOUT = 25          # PDFは1本ずつ多いので短く諦める。90秒×50本で1時間止まった
FAIL_STREAK = 3           # 同じ収集先で続けてこれだけ失敗したら、今日はその収集先をやめる
MAX_BYTES = 20 * 1024 * 1024      # 1本がこれより大きければ見送る
PDF_MAX_BYTES = 2 * 1024 * 1024   # PDFはこれより大きければ見送る（資料の束を避ける）
WANT = re.compile(r"\.(xlsx|xls|csv)(\?|$)", re.I)
WANT_PDF = re.compile(r"\.pdf(\?|$)", re.I)

# PDFは数が多いので、リンクの文字で中身かどうかを見分ける。
# 大阪狭山市と泉佐野市は「手引き」「要綱」「しおり」「フロー図」しか無く、
# 一覧だと思って落とすと手続きの説明書が溜まるだけだった。
PDF_IS_DATA = re.compile(r"概要|一覧|リスト|届出状況|縦覧|告示")
PDF_NOT_DATA = re.compile(r"手引|要綱|しおり|フロー|意見書|様式|記入例|チェックリスト|指針")

# 収集先ごとに、どのラベルが中身かを sources.json の pdf_labels で指定できる。
# 兵庫県は全部「資料」、神戸市は「届出書」で、上の一般則では拾えない。
# 大きさは PDF_MAX_BYTES（2MB）で切るので、図面つきの重いものは自然に外れる。
PDF_LABEL_RULE = {}
_current_source = None

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
    """保存ページから Excel/CSV（や PDF）のリンクを拾う（重複は除く）。

    PDFのときは、リンクの文字から中身かどうかも見る。
    """
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
        label = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(2))).strip()
        if want is WANT_PDF:
            if PDF_NOT_DATA.search(label):
                continue
            # 収集先ごとの決まり（兵庫県は「資料」、神戸市は「届出書」が中身）
            rule = PDF_LABEL_RULE.get(_current_source) if _current_source else None
            if rule:
                if not re.search(rule, label):
                    continue
            elif not PDF_IS_DATA.search(label):
                continue
        seen.add(url)
        out.append((url, label[:60]))
    return out


def safe_name(url):
    """URL から、そのまま置けるファイル名を作る。"""
    name = os.path.basename(urllib.parse.urlparse(url).path) or "file"
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    return name[:100]


def browser_session(page_url):
    """ページを先に開いて、サーバーがくれるクッキーを持った状態を作る。

    大阪市はURLの組み立てが正しくブラウザからは落とせるのに、この仕組みからは
    404を返す。ページを見ずにいきなりファイルを取りに来る相手を弾いている
    可能性がある。人がブラウザでするのと同じ順（ページ→リンク）でたどる。
    名乗り（User-Agent）は変えない。
    """
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req = urllib.request.Request(page_url, headers={
        "User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "ja,en;q=0.5"})
    try:
        opener.open(req, timeout=TIMEOUT).read(200000)
    except Exception:
        pass
    return opener


def download(url, dest, limit=MAX_BYTES, referer=None, timeout=TIMEOUT, opener=None):
    """ファイルを落とす。

    大阪市はURLの組み立てが正しいのに404を返した（大阪府は同じやり方で17本
    取れている）。ファイルを配るときに参照元を見るサーバーがあるので、
    どのページから来たのかを添える。素性は User-Agent に書いてあるとおり。
    """
    headers = {"User-Agent": UA, "Accept-Language": "ja,en;q=0.5", "Accept": "*/*",
               "Accept-Encoding": "identity"}
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    open_ = opener.open if opener else urllib.request.urlopen
    with open_(req, timeout=timeout) as r:
        size = int(r.headers.get("Content-Length") or 0)
        if size > limit:
            raise ValueError(f"大きすぎる（{size:,}バイト）ので見送った")
        data = r.read(limit + 1)
    if len(data) > limit:
        raise ValueError("大きすぎるので見送った")
    with open(dest, "wb") as f:
        f.write(data)
    return len(data)


def recheck(url, dest, src, opener):
    """手持ちがあるファイルを、もう一度取りに行って結果を一行で返す。

    失敗しても手持ちはそのまま。取れて中身が変わっていたときだけ置き換える。
    """
    tmp = dest + ".new"
    try:
        n = download(url, tmp, MAX_BYTES, referer=src["url"], timeout=TIMEOUT, opener=opener)
    except (ValueError, urllib.error.HTTPError, urllib.error.URLError, OSError, TimeoutError) as e:
        if os.path.exists(tmp):
            os.remove(tmp)
        return f"  - 手持ちあり {safe_name(url)} — 取り直し {type(e).__name__}: {str(e)[:60]}（手持ちを使う）"
    with open(tmp, "rb") as f:
        new = f.read()
    with open(dest, "rb") as f:
        old = f.read()
    if new == old:
        os.remove(tmp)
        return f"  - 手持ちあり {safe_name(url)} — 取り直せた（{n:,}バイト、中身は同じ）"
    os.replace(tmp, dest)
    return f"  - **{safe_name(url)}** 取り直せた（{n:,}バイト、中身が変わっていたので置き換えた）"


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
    if not path.lower().endswith((".xlsx", ".xls")):
        return None
    try:
        sheets = xlsx.read_any(path)
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
                              if s.startswith("osaka") or v.get("pdf") or v.get("files")]
    lines = ["# Excelを取ってきた結果", ""]
    got = skipped = failed = 0

    for sid in wanted:
        src = sources.get(sid)
        if not src or not src.get("url"):
            continue
        global _current_source
        _current_source = sid
        if src.get("pdf_labels"):
            PDF_LABEL_RULE[sid] = src["pdf_labels"]
        raw = newest_raw(sid)
        if not raw:
            lines.append(f"### {src['name']}\n\n- まだページを保存していない\n")
            continue

        # 参考ソース（規約ページなど）は、そのページのExcel/CSVは要らない。
        # 兵庫県オープンデータの入口で、犯罪統計など117本を落としてしまったことがある
        links = [] if (src.get("area") == "ref" and not src.get("files")) else excel_links(raw, src["url"])
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

        streak = 0
        opener = browser_session(src["url"]) if src.get("session") else None
        for url, label in links:
            dest = os.path.join(d, safe_name(url))
            if os.path.exists(dest):
                if opener is not None:
                    # クッキー経路の収集先は、手持ちがあっても取りに行って通るかを確かめる。
                    # 大阪市は利用者がブラウザで落としたファイルを同じ名前で置いてあるので、
                    # 飛ばすと「通るようになったか」がいつまでも分からない。
                    # 取れて中身が変わっていれば置き換える（更新の検知にもなる）
                    lines.append(recheck(url, dest, src, opener))
                    time.sleep(WAIT)
                skipped += 1
                continue
            is_pdf = url.lower().endswith(".pdf")
            # 収集先ごとにPDFの上限を変えられる（兵庫県の資料は8MB級が本体）
            pdf_cap = int(src.get("pdf_max_mb", 0) * 1024 * 1024) or PDF_MAX_BYTES
            try:
                n = download(url, dest,
                             pdf_cap if is_pdf else MAX_BYTES,
                             referer=src["url"],
                             timeout=PDF_TIMEOUT if is_pdf else TIMEOUT,
                             opener=opener)
            except ValueError as e:
                # 「大きすぎるので見送った」は相手の不調ではない。失敗の連続には数えない。
                # 兵庫県はリストの先頭3本が8MB級で、ここを失敗と数えて全部打ち切っていた
                lines.append(f"  - 見送り {safe_name(url)} — {e}")
                skipped += 1
                continue
            except (urllib.error.HTTPError, urllib.error.URLError, OSError, TimeoutError) as e:
                lines.append(f"  - 取れなかった {safe_name(url)} — {type(e).__name__}: {str(e)[:60]}")
                if opener is not None:
                    # 大阪市は機械からは取れないと分かっている（2026-09-12時点）。
                    # ページに新しいファイル名が出たら、人がブラウザで落として置く合図にする
                    lines.append(f"  - **新しいファイル名 {safe_name(url)} がページに出ています。"
                                 f"ブラウザで落として data/files/{sid}/ に置いてください**")
                failed += 1
                streak += 1
                if streak >= FAIL_STREAK:
                    left = sum(1 for u, _ in links if not os.path.exists(os.path.join(d, safe_name(u))))
                    lines.append(f"  - **{FAIL_STREAK}回続けて取れなかったので、この収集先は今日はここまで**（残り{left}本は次回）")
                    break
                time.sleep(WAIT)
                continue
            streak = 0
            got += 1
            lines.append(f"  - **{safe_name(url)}** {n:,}バイト … {label}")
            info = peek(dest)
            if info is None:
                lines.append("    - 中は読んでいない")
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
