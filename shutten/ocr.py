#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""紙をスキャンしたPDFから文字を起こす（OCR）。

兵庫県の「資料」PDFは33本中32本が画像で、pdf.py では文字が取れなかった。
神戸市の「届出書」も様式に1文字ずつ置かれていて表にならない。
ここでは Tesseract（日本語）で最初の2ページだけ読む。届出書の1枚目に
名称・所在地・届出者・届出の種類が書いてあり、あとは図面や添付なので要らない。

出力
  data/ocr/<id>/<ファイル名>.txt … 起こした文字そのまま
  data/ocr/<id>.json             … そこから拾った項目（名称・所在地・届出者・種類・日付・面積）

要るもの: tesseract（jpn）と pdftoppm（poppler-utils）。無ければ理由を出して何もしない。
1本1.5秒くらい。8MB級（30ページ超）でも最初の2ページしか描かないので同じ。
"""

import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = os.path.join(HERE, "data", "files")
OUT = os.path.join(HERE, "data", "ocr")
PAGES = 2
DPI = 200

sys.path.insert(0, HERE)
import pdf as pdflib  # noqa: E402


def have_tools():
    missing = [t for t in ("tesseract", "pdftoppm") if not shutil.which(t)]
    if missing:
        return False, f"{', '.join(missing)} が無い（apt-get install tesseract-ocr tesseract-ocr-jpn poppler-utils）"
    langs = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True).stdout
    if "jpn" not in langs:
        return False, "tesseract に日本語（jpn）が入っていない"
    return True, ""


def ocr_pdf(path):
    """最初の PAGES ページを描いて読む。文字が埋まっているPDFならそちらを使う。"""
    try:
        rows = pdflib.extract_rows(path)
    except Exception:
        rows = []
    if rows and sum(len("".join(r)) for r in rows) > 80:
        return "\n".join(" ".join(r) for r in rows), "embedded"
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-r", str(DPI), "-f", "1", "-l", str(PAGES), "-png", path, os.path.join(td, "p")],
                       capture_output=True, timeout=120)
        texts = []
        for png in sorted(glob.glob(os.path.join(td, "p-*.png"))):
            r = subprocess.run(["tesseract", png, "stdout", "-l", "jpn", "--psm", "6"],
                               capture_output=True, text=True, timeout=120)
            texts.append(r.stdout)
    return "\n".join(texts), "ocr"


# 届出書の1枚目から拾う項目。OCRは「!」「昌」のような誤読があるので、ゆるく拾う
PAT = {
    "form":      r"様式第\s*(\d+)",
    "article":   r"第\s*(\d+)\s*条\s*第\s*(\d+)\s*項",
    "date":      r"(令和|平成)\s*(\d{1,2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*[日昌曰]",
    "store":     r"名\s*称\s*[:：]\s*([^\n]{2,40})",
    "address":   r"所\s*在\s*地\s*[:：]\s*([^\n]{2,50})",
    "area":      r"店舗面積[^\d]{0,12}([\d,，]{3,7})\s*(?:㎡|m2|平方)",
    "content":   r"変更\s*した\s*事項\s*\n?([^\n]{2,60})",
}
KIND_BY_FORM = {"1": "新設", "2": "変更", "3": "廃止"}   # 大店立地法施行規則の様式番号


def pick(text):
    out = {}
    m = re.search(PAT["form"], text)
    if m:
        out["form"] = m.group(1)
        out["kind_guess"] = KIND_BY_FORM.get(m.group(1), "")
    m = re.search(PAT["article"], text)
    if m:
        out["article"] = f"第{m.group(1)}条第{m.group(2)}項"
    m = re.search(PAT["date"], text)
    if m:
        base = {"令和": 2018, "平成": 1988}[m.group(1)]
        out["date"] = f"{base + int(m.group(2)):04d}-{int(m.group(3)):02d}-{int(m.group(4)):02d}"
    for k in ("store", "address", "area", "content"):
        m = re.search(PAT[k], text)
        if m:
            out[k] = m.group(1).strip()
    # 届出者＝「兵庫県知事」「神戸市長」の次の行にある会社名
    m = re.search(r"(?:知事|市長)\s*[殿様欄]?\s*\n\s*([^\n]{3,40}(?:株式会社|有限会社|協同組合|㈱)[^\n]{0,20}|(?:株式会社|有限会社|㈱)[^\n]{2,30})", text)
    if m:
        out["applicant"] = m.group(1).strip()
    return out


def main():
    ok, why = have_tools()
    if not ok:
        print(f"OCRはしない: {why}")
        return
    with open(os.path.join(HERE, "sources.json"), encoding="utf-8") as f:
        srcs = [s for s in json.load(f)["sources"] if s.get("pdf") and s.get("enabled")]
    only = sys.argv[1] if len(sys.argv) > 1 else None

    lines = ["# OCRの結果", ""]
    for s in srcs:
        sid = s["id"]
        if only and only != sid:
            continue
        pdfs = sorted(glob.glob(os.path.join(FILES, sid, "*.pdf")))
        if not pdfs:
            continue
        d = os.path.join(OUT, sid)
        os.makedirs(d, exist_ok=True)
        done = new = fail = 0
        picked = {}
        jpath = os.path.join(OUT, f"{sid}.json")
        if os.path.exists(jpath):
            with open(jpath, encoding="utf-8") as f:
                picked = json.load(f)
        for p in pdfs:
            stem = os.path.splitext(os.path.basename(p))[0]
            tpath = os.path.join(d, stem + ".txt")
            if os.path.exists(tpath):
                done += 1
                if stem not in picked:
                    picked[stem] = pick(open(tpath, encoding="utf-8").read())
                continue
            try:
                text, how = ocr_pdf(p)
            except Exception as e:
                fail += 1
                lines.append(f"  - {stem}: 失敗 {type(e).__name__}")
                continue
            with open(tpath, "w", encoding="utf-8") as f:
                f.write(text)
            picked[stem] = pick(text)
            picked[stem]["how"] = how
            new += 1
        with open(jpath, "w", encoding="utf-8") as f:
            json.dump(picked, f, ensure_ascii=False, indent=1)
        got_store = sum(1 for v in picked.values() if v.get("store"))
        lines.append(f"- **{s['name']}**: 新しく読んだ {new}本 / 読んであった {done}本 / 失敗 {fail}本 / 店名が拾えた {got_store}/{len(picked)}")
    text = "\n".join(lines)
    print(text)
    gh = os.environ.get("GITHUB_STEP_SUMMARY")
    if gh:
        with open(gh, "a", encoding="utf-8") as f:
            f.write("\n" + text + "\n")


if __name__ == "__main__":
    main()
