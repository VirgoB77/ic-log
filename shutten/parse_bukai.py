"""兵庫県 まちづくり審議会 大規模小売店舗等立地部会の議案PDFから、届出の記録を取り出す。

議案書の冒頭に「１ 届出内容」があり、
  （新設 届出年月日：平成 29 年２月 28 日 根拠条文：法 5-1 …）
  （変更 届出年月日：平成 20 年 12 月 26 日 根拠条文：法 6-2）   ← 同じ店の過去の届出も並ぶ
  名 称   （仮称）マックスバリュ南今宿店
  所在地  姫路市南今宿 1600 番地２ほか
  設置者  マックスバリュ西日本株式会社
  小売業者の名称（業態）  …
  新設年月日  平成 29 年 10 月 29 日
  店舗面積、延べ面積、  1,532 ㎡、2,072 ㎡
と続く。1 行の「届出年月日」が 1 件の届出。部会にかかるのは新設と主な変更だけだが、
兵庫県の縦覧ページに過去分が無いので、2007 年ごろまでさかのぼれる貴重な手がかり。

「基本計画書の内容」で始まる議案は大規模集客施設条例の案件（届出の前の計画段階）なので、
ここでは扱わない（別の棚に置く候補）。

PDF の文字起こしは pdftotext（poppler）を使う。標準ライブラリの pdf.py ではこのPDFの
文字が取れなかった。

使い方: python3 shutten/parse_bukai.py
出力:   data/parsed/hyogo-bukai/all.json（過去分を全部含む一覧として merge.py が読む）
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parse as P  # noqa: E402  to_iso / make_key / means_of を借りる

SRC = os.path.join(HERE, "data", "files", "hyogo-bukai")
OUT = os.path.join(HERE, "data", "parsed", "hyogo-bukai")
DOC_BASE = "https://web.pref.hyogo.lg.jp/ks21/documents/"
SOURCE = "hyogo-bukai"

Z2H = str.maketrans("０１２３４５６７８９（）：，、．－", "0123456789():,,.-")


def norm(s):
    """全角数字を半角に、空白を落とす。「平成 29 年２月 28 日」→「平成29年2月28日」"""
    return re.sub(r"[\s　]+", "", (s or "").translate(Z2H))


def text_of(path):
    if not shutil.which("pdftotext"):
        raise RuntimeError("pdftotext が無い（poppler-utils を入れる）")
    r = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, timeout=120)
    return r.stdout.decode("utf-8", errors="replace")


DATE = r"((?:平成|令和|昭和)?\s*[0-9０-９元]+\s*年\s*[0-9０-９]+\s*月\s*[0-9０-９]+\s*日)"
NOTICE_LINE = re.compile(
    r"(新設|変更|廃止|承継)?\s*届出年月日\s*[：:]\s*" + DATE + r"\s*(?:[、,]\s*)?"
    r"(?:根拠条文\s*[：:]\s*法\s*第?\s*([0-9０-９]+)\s*(?:条|[-‐−‑])\s*第?\s*([0-9０-９]+)\s*項?)?")
KV = re.compile(r"^\s*(\S.*?\S)\s{2,}(\S.*?)\s*$")   # 「所   在 地        姫路市…」を 見出し / 値 に割る


def parse_block(block, meeting, pdf_name):
    """1 議案分の文字から、届出の記録を返す。条例（基本計画書）の議案なら空。"""
    if "届出内容" not in block and "届出の内容" not in block:
        return []
    lines = block.splitlines()
    notices = []
    fields = {}
    for ln in lines[:60]:                       # 冒頭の表だけ見る
        for m in NOTICE_LINE.finditer(ln):
            kind, raw, jo, ko = m.group(1), m.group(2), m.group(3), m.group(4)
            d = P.to_iso(norm(raw))
            if not d:
                continue
            article = f"第{norm(jo)}条第{norm(ko)}項" if jo else ""
            notices.append({"kind_word": kind or "", "notified_on": d, "article": article, "raw": raw.strip()})
        km = KV.match(ln)
        if km:
            k = norm(km.group(1))
            v = km.group(2).strip()
            if k.startswith("名称") and "store" not in fields:
                # 「（仮称）ハローズ砥堀店：新設」「イオンモール伊丹：駐車場の出入口の変更」「阪急西宮ガーデンズ」
                store, _, tail = v.partition("：") if "：" in v else v.partition(":")
                fields["store"] = store.strip()
                tail = tail.strip()
                if tail in ("新設", "変更", "廃止", "承継"):
                    fields["kind_hint"] = tail
                elif tail:
                    fields["content"] = tail
                    fields["kind_hint"] = "変更"
            elif k.startswith("所在地") and "address" not in fields:
                fields["address"] = re.sub(r"\s+", "", v)
            elif k.startswith("設置者") and "operator" not in fields:
                fields["operator"] = v
            elif k.startswith("小売業者") and "retailer" not in fields:
                fields["retailer"] = re.sub(r"[（(][^）)]*[）)]\s*$", "", v).strip()
            elif k in ("新設年月日", "変更年月日") and "event_on" not in fields:
                fields["event_on"] = P.to_iso(norm(v))
                fields["event_kind"] = "新設" if k.startswith("新設") else "変更"
            elif k.startswith("店舗面積") and "area_m2" not in fields:
                am = re.search(r"([\d,]+)\s*㎡", v)
                if am:
                    fields["area_m2"] = int(am.group(1).replace(",", ""))
    store = fields.get("store")
    if not store or not notices:
        return []
    out = []
    for n in notices:
        kind_word = n["kind_word"] or fields.get("kind_hint") or ""
        article = n["article"] or ("第5条第1項" if kind_word == "新設" else "")
        kind = P.means_of(article) if article else (kind_word or "不明")
        rec = {
            "article": article,
            "kind": kind,
            "notified_on": n["notified_on"],
            "notified_raw": n["raw"],
            "store": store,
            "address": fields.get("address", ""),
            "operator": fields.get("operator", ""),
            "retailer": fields.get("retailer", ""),
            "content": fields.get("content", "") if kind == "変更" else "",
            "area_m2": fields.get("area_m2"),
            "event_on": fields.get("event_on") if fields.get("event_kind") == kind else None,
            "meeting": meeting,
            "docs": [DOC_BASE + pdf_name],
            "source": SOURCE,
        }
        rec["key"] = P.make_key(SOURCE, rec)
        out.append(rec)
    return out


def main():
    files = sorted(glob.glob(os.path.join(SRC, "*gian*.pdf")))
    recs, seen = [], set()
    lines = ["# 部会の議案から取り出した届出", ""]
    per_meeting = []
    for path in files:
        name = os.path.basename(path)
        mm = re.match(r"(\d+)", name)
        meeting = f"第{mm.group(1)}回" if mm else name
        try:
            text = text_of(path)
        except Exception as e:
            lines.append(f"- {name}: 読めなかった — {type(e).__name__}: {str(e)[:60]}")
            continue
        # 「議案１」「議案 ２」で区切る。区切りが無ければ全体を 1 つとして見る
        blocks = re.split(r"\n(?=\s*議\s*案\s*[0-9０-９]+\s*\n)", "\n" + text)
        got = 0
        for b in blocks:
            for r in parse_block(b, meeting, name):
                if r["key"] in seen:            # 同じ店の過去の届出は複数の回に出てくる
                    continue
                seen.add(r["key"])
                recs.append(r)
                got += 1
        per_meeting.append((meeting, got))
    recs.sort(key=lambda r: (r["notified_on"], r["store"]))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "all.json"), "w", encoding="utf-8") as f:
        json.dump(recs, f, ensure_ascii=False, indent=1)
    kinds = {}
    for r in recs:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    years = {}
    for r in recs:
        years[r["notified_on"][:4]] = years.get(r["notified_on"][:4], 0) + 1
    lines.insert(1, f"**{len(recs)} 件**（" + " / ".join(f"{k} {n}" for k, n in sorted(kinds.items(), key=lambda x: -x[1])) +
                 f"）。議案PDF {len(files)} 本。届出年：" + ", ".join(f"{y} {n}" for y, n in sorted(years.items())))
    lines += [f"- {m}: {g} 件" for m, g in per_meeting if g]
    text = "\n".join(lines)
    with open(os.path.join(HERE, "data", "bukai-report.md"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    gh = os.environ.get("GITHUB_STEP_SUMMARY")
    if gh:
        with open(gh, "a", encoding="utf-8") as f:
            f.write("\n" + text + "\n")


if __name__ == "__main__":
    main()
