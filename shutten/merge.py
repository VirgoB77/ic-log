#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""日ごとに取り出した届出を、1件1行にまとめる。

data/parsed/<id>/<日付>.json は「その日にページに載っていたもの」。
毎日とるので、同じ届出が日の数だけ並ぶ。ここで目印（key）ごとにまとめて、

  first_seen … はじめて見た日
  last_seen  … 最後に見た日
  listed     … 最新の保存日にまだ載っているか

を付ける。listed が false になった瞬間が「縦覧が終わってページから消えた」
ということで、この仕組みの芯になる。消えたあとも、ここには残る。

大阪市・大阪府のExcelは過去分を全部含む累積の一覧なので、消える／消えない
の対象にはしない（mode を cumulative にする）。

出力
  data/all.json    … 全件（1件1行）
  data/summary.md  … 収集先ごとの件数と、消えたものの一覧
"""

import glob
import json
import os
import re
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PARSED = os.path.join(HERE, "data", "parsed")
OUT_ALL = os.path.join(HERE, "data", "all.json")
OUT_SUM = os.path.join(HERE, "data", "summary.md")

DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CUMULATIVE = {"osaka-city", "osaka-pref"}   # 過去分を全部含む一覧を出している収集先


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    by_key = {}
    latest_day = {}                     # 収集先ごとの、いちばん新しい保存日

    for src_dir in sorted(glob.glob(os.path.join(PARSED, "*"))):
        src = os.path.basename(src_dir)
        files = sorted(glob.glob(os.path.join(src_dir, "*.json")))
        if not files:
            continue
        cumulative = src in CUMULATIVE

        for path in files:
            stem = os.path.splitext(os.path.basename(path))[0]
            day = stem if DAY.match(stem) else None
            if day and not cumulative:
                latest_day[src] = max(latest_day.get(src, ""), day)
            for rec in load(path):
                k = rec["key"]
                cur = by_key.get(k)
                if cur is None:
                    rec = dict(rec)
                    rec["first_seen"] = day
                    rec["last_seen"] = day
                    rec["mode"] = "cumulative" if cumulative else "snapshot"
                    by_key[k] = rec
                else:
                    # あとの日のほうを本体にし、はじめて見た日は残す
                    first = cur.get("first_seen")
                    newer = dict(rec)
                    newer["first_seen"] = min(first, day) if (first and day) else (first or day)
                    newer["last_seen"] = max(cur.get("last_seen") or "", day or "") or None
                    newer["mode"] = cur["mode"]
                    by_key[k] = newer

    # 最新の保存日に載っているか
    for rec in by_key.values():
        if rec["mode"] == "snapshot":
            rec["listed"] = (rec["last_seen"] == latest_day.get(rec["source"]))
        else:
            rec["listed"] = True

    all_recs = sorted(by_key.values(),
                      key=lambda r: (r.get("notified_on") or "", r["source"], r["store"]), reverse=True)
    with open(OUT_ALL, "w", encoding="utf-8") as f:
        json.dump(all_recs, f, ensure_ascii=False, indent=1)

    # ---- まとめ ----
    lines = [f"# まとめ（{len(all_recs):,} 件）", ""]
    lines.append("| 収集先 | 件数 | 新設 | 変更 | 廃止 | 承継 | 最新の保存日 | 消えた |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |")
    per = defaultdict(list)
    for r in all_recs:
        per[r["source"]].append(r)
    gone_all = []
    for src in sorted(per):
        rs = per[src]
        kinds = Counter(r["kind"] for r in rs)
        gone = [r for r in rs if r["mode"] == "snapshot" and not r["listed"]]
        gone_all += gone
        lines.append(f"| {src} | {len(rs)} | {kinds.get('新設',0)} | {kinds.get('変更',0)} | "
                     f"{kinds.get('廃止',0)} | {kinds.get('承継',0)} | {latest_day.get(src,'—')} | {len(gone)} |")
    lines.append("")

    if gone_all:
        lines.append("## ページから消えた届出（縦覧が終わったもの）")
        lines.append("")
        lines.append("| 最後に見た日 | 収集先 | 種類 | 店舗 | 届出日 |")
        lines.append("| --- | --- | --- | --- | --- |")
        for r in sorted(gone_all, key=lambda r: r["last_seen"], reverse=True)[:50]:
            lines.append(f"| {r['last_seen']} | {r['source']} | {r['kind']} | {r['store']} | {r['notified_on']} |")
        lines.append("")

    # これから起きること
    today = max(latest_day.values()) if latest_day else ""
    future = [r for r in all_recs if (r.get("event_on") or r.get("planned_on") or "") > today]
    if future:
        lines.append(f"## これから起きる予定（{len(future)} 件）")
        lines.append("")
        lines.append("| 予定日 | 種類 | 市区 | 店舗 | 面積㎡ |")
        lines.append("| --- | --- | --- | --- | ---: |")
        for r in sorted(future, key=lambda r: r.get("event_on") or r.get("planned_on"))[:40]:
            place = r.get("city") or r.get("ward") or r.get("address", "")[:8]
            lines.append(f"| {r.get('event_on') or r.get('planned_on')} | {r['kind']} | {place} | {r['store']} | {r.get('area_m2') or ''} |")
        lines.append("")

    with open(OUT_SUM, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines[:14]))
    print(f"\n→ {OUT_ALL} と {OUT_SUM} に書いた")

    gh = os.environ.get("GITHUB_STEP_SUMMARY")
    if gh:
        with open(gh, "a", encoding="utf-8") as f:
            f.write("\n" + "\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
