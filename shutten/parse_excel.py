#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Excelで出している自治体の届出を、1件ずつ取り出す。

parse.py はHTMLの表を読む。こちらは data/files/ に落としたExcelを読んで、
同じ形（data/parsed/<id>/<日付>.json）に書き出す。

いまは大阪市の届出一覧（to*.xls）。平成12年の法施行からの全届出が1枚に入っていて、
75列ある。HTMLの表には無い項目（面積・設置者・小売業者・開店日・住民意見・
本市意見・同じ店の履歴）が取れるので、取れるものは全部持っておく。

日付はファイル名の日付（to20260630 → 2026-06-30 時点）を使う。
"""

import glob
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = os.path.join(HERE, "data", "files")
OUT = os.path.join(HERE, "data", "parsed")

sys.path.insert(0, HERE)
import xlsx  # noqa: E402
from parse import coerce_date_column, to_iso, means_of  # noqa: E402


# 大阪市の「届出区分」の書き方 → 条文と種類
KUBUN = {
    "新5-1": ("第5条第1項", "新設"),
    "変6-1": ("第6条第1項", "変更"),
    "変6-2": ("第6条第2項", "変更"),
    "附5-1": ("附則第5条第1項", "変更"),
    "承11-3": ("第11条第3項", "承継"),
    "廃止": ("第6条第5項", "廃止"),
    "通8-7": ("第8条第7項", "意見・勧告"),
    "変8-7": ("第8条第7項", "意見・勧告"),
}


def find_header(rows, must="整理番号"):
    for i, r in enumerate(rows[:10]):
        if any(must in c for c in r):
            return i
    return None


def col(idx, r, name, default=""):
    i = idx.get(name)
    return clean(r[i]) if i is not None and i < len(r) else default


# 役所の「空」の書き方はいろいろある。全部 空 として扱う
EMPTY = {"", "－", "-", "―", "‐", "ー", "なし", "無", "0", "1899-12-31"}


def clean(v):
    """空を表す記号を空文字にそろえる。"""
    v = (v or "").strip()
    if v in EMPTY or v.startswith("1899-12-3"):     # Excelの「空の日付」は 1899-12-30/31 で出る
        return ""
    return v


def num(s):
    """「1,234」「1234.0」を数に。空や記号は None。"""
    s = clean(s).replace(",", "")
    if not s:
        return None
    try:
        f = float(s)
        return int(f) if f == int(f) else f
    except ValueError:
        return None


def make_key(source, article, notified_on, store):
    seed = f"{source}|{article}|{notified_on}|{store}"
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]


def asof_from_name(path):
    m = re.search(r"(20\d{2})(\d{2})(\d{2})", os.path.basename(path))
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


# ------------------------------------------------------------- 大阪市

def parse_osaka_city(path):
    sheets = xlsx.read_any(path)
    rows = next(iter(sheets.values()))
    rows = coerce_date_column(rows)
    h = find_header(rows)
    if h is None:
        return []
    hdr = [c.strip() for c in rows[h]]
    idx = {}
    for i, c in enumerate(hdr):
        # 「駐車場\n位置変更」のように改行が入るので、つぶして一致させる
        idx.setdefault(re.sub(r"\s", "", c), i)

    def g(r, name):
        return col(idx, r, name)

    hist_cols = [idx[k] for k in idx if re.fullmatch(r"履歴\d+", k)]
    hist_cols.sort()

    recs = []
    for r in rows[h + 1:]:
        ref = g(r, "整理番号")
        store = g(r, "店舗名称")
        if not ref or not store:
            continue
        kubun = g(r, "届出区分")
        article, kind = KUBUN.get(kubun, ("", means_of(kubun) if kubun else "不明"))
        notified = to_iso(g(r, "届出日")) or g(r, "届出日") or None

        rec = {
            "source": "osaka-city",
            "ref": ref,                              # 整理番号（大阪市がふった番号）
            "store_no": g(r, "店舗番号"),
            "article": article,
            "kind": kind,
            "kubun_raw": kubun,
            "notified_on": notified,
            "store": store,
            "ward": g(r, "区名"),
            "address": g(r, "店舗所在地（地番又は住居表示）"),
            "area_m2": num(g(r, "店舗面積")),
            "floor_area_m2": num(g(r, "延床面積")),
            "planned_on": to_iso(g(r, "新設(変更）予定日")),
            "opened_on": to_iso(g(r, "開店日")),
            "content": g(r, "届出内容"),
            "operator": g(r, "設置者名称"),
            "retailer": g(r, "小売業者名称(主)"),
            "parking": num(g(r, "駐車")),
            "bicycle": num(g(r, "駐輪（原付含む）")),
            "open_time": g(r, "開店時間(主)"),
            "close_time": g(r, "閉店時間(主)"),
            "zoning": g(r, "用途地域"),
            "citizen_opinion": g(r, "住民等意見"),
            "city_opinion": g(r, "本市意見"),
            "city_recommendation": g(r, "本市勧告"),
            "history": [r[i] for i in hist_cols if i < len(r) and r[i]],
            "note": g(r, "備考"),
        }
        # 整理番号は大阪市がふった一意の番号なので、そのまま目印にする。
        # 店名と日付だけだと、同じ日に同じ店が2件出したときにぶつかる（9組あった）
        rec["key"] = make_key("osaka-city", article, notified, f"{store}|{ref}")
        recs.append(rec)
    return recs


SOURCES = {
    "osaka-city": ("to*.xls", parse_osaka_city),
}


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    lines = ["# Excelから取り出した結果", ""]
    for sid, (pattern, fn) in SOURCES.items():
        if only and only != sid:
            continue
        for path in sorted(glob.glob(os.path.join(FILES, sid, pattern))):
            asof = asof_from_name(path) or "unknown"
            recs = fn(path)
            d = os.path.join(OUT, sid)
            os.makedirs(d, exist_ok=True)
            out = os.path.join(d, f"{asof}.json")
            with open(out, "w", encoding="utf-8") as f:
                json.dump(recs, f, ensure_ascii=False, indent=1)
            kinds = {}
            for r in recs:
                kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
            k = " / ".join(f"{a} {b}件" for a, b in sorted(kinds.items(), key=lambda x: -x[1]))
            lines.append(f"- {sid} {os.path.basename(path)}（{asof}時点）: **{len(recs)}件**（{k}）")
    text = "\n".join(lines)
    print(text)
    gh = os.environ.get("GITHUB_STEP_SUMMARY")
    if gh:
        with open(gh, "a", encoding="utf-8") as f:
            f.write("\n" + text + "\n")


if __name__ == "__main__":
    main()
