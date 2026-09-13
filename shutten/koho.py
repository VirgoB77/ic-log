"""兵庫県公報の検索用目録（Excel）から、大規模小売店舗立地法の公告を数える。

兵庫県は 2007 年 1 月からの公報の目録を年ごとの Excel で出している。
「公告」シートに 1 行 1 公告で、件名・担当課・発行日・公報番号が載る。
件名に店舗名は無いが、「大規模小売店舗の新設に関する届出」「…変更に関する届出」
「…廃止に関する届出」「市町の意見の概要」の別と、公告日（＝縦覧開始日）、
担当（県庁の都市計画課か、どの県民局か）は分かる。

ここから作るもの：
- data/koho/hyogo-notices.json … 公告 1 件 1 行（日付・種類・担当・公報番号・件名）
- data/koho/hyogo-monthly.json … 年月 × 種類 の件数

店舗名まで要るときは、公報番号から公報本体の PDF をたどる（それは次の段）。
"""
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xlsx  # noqa: E402

SRC = os.path.join(HERE, "data", "files", "hyogo-koho-mokuroku")
OUT = os.path.join(HERE, "data", "koho")

KIND = [
    (r"新設に関する届出", "新設"),
    (r"変更に関する届出", "変更"),
    (r"廃止に関する届出", "廃止"),
    (r"取下げ", "取下げ"),
    (r"市町等?の意見", "市町の意見"),
    (r"県の意見に対して講ずる措置", "措置"),
    (r"県の意見", "県の意見"),
    (r"住民等?の意見", "住民の意見"),
]


def kind_of(title):
    t = re.sub(r"\s", "", title)
    for pat, name in KIND:
        if re.search(pat, t):
            return name
    return "その他"


def to_iso(v):
    """'2007-01-09' / '46007'（Excel の通し番号）/ '2007/1/9' → 'YYYY-MM-DD'"""
    s = str(v or "").strip()
    if not s:
        return ""
    m = re.match(r"^(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})", s)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    if re.match(r"^\d{4,6}(\.0+)?$", s):
        n = int(float(s))
        if 30000 < n < 60000:                       # 1982〜2064 年
            return (date(1899, 12, 30) + timedelta(days=n)).isoformat()
    return ""


def rows_of(path):
    """1 冊の目録から、大店立地法の公告の行だけ返す。"""
    sheets = xlsx.read_any(path)
    out = []
    for name, rows in sheets.items():
        if "公告" not in name or "企業庁" in name:
            continue
        hdr = next((i for i, r in enumerate(rows[:8])
                    if any("件" in str(c) and "名" in str(c) for c in r)), None)
        if hdr is None:
            continue
        head = [re.sub(r"\s", "", str(c or "")) for c in rows[hdr]]
        ci = {h: i for i, h in enumerate(head) if h}

        def col(cells, *keys):
            for k in keys:
                i = ci.get(k)
                if i is not None and i < len(cells):
                    return str(cells[i] or "").strip()
            return ""

        for r in rows[hdr + 1:]:
            cells = list(r)
            title = col(cells, "件名")
            if "大規模小売" not in title:
                continue
            out.append({
                "date": to_iso(col(cells, "発行日", "発行年月日")),
                "kind": kind_of(title),
                "dept": col(cells, "担当課等", "担当課"),
                "no": col(cells, "公報番号", "公報号数", "号数"),
                "title": re.sub(r"\s+", " ", title),
                "sheet": name,
                "file": os.path.basename(path),
            })
    return out


def main():
    files = sorted(glob.glob(os.path.join(SRC, "*.xls")) + glob.glob(os.path.join(SRC, "*.xlsx")))
    notices = []
    lines = ["# 兵庫県公報の目録から数えた大店立地法の公告", ""]
    for p in files:
        try:
            got = rows_of(p)
        except Exception as e:                      # 1 冊読めなくても他は進める
            lines.append(f"- {os.path.basename(p)}: 読めなかった — {type(e).__name__}: {str(e)[:60]}")
            continue
        notices.extend(got)
        years = Counter(g["date"][:4] for g in got if g["date"])
        lines.append(f"- {os.path.basename(p)}: {len(got)} 件（{', '.join(f'{y}年 {n}' for y, n in sorted(years.items()))}）")

    notices.sort(key=lambda g: (g["date"], g["no"], g["kind"]))
    monthly = defaultdict(Counter)
    for g in notices:
        if g["date"]:
            monthly[g["date"][:7]][g["kind"]] += 1
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "hyogo-notices.json"), "w", encoding="utf-8") as f:
        json.dump(notices, f, ensure_ascii=False, indent=0)
    with open(os.path.join(OUT, "hyogo-monthly.json"), "w", encoding="utf-8") as f:
        json.dump({ym: dict(c) for ym, c in sorted(monthly.items())}, f, ensure_ascii=False, indent=0)

    kinds = Counter(g["kind"] for g in notices)
    undated = sum(1 for g in notices if not g["date"])
    lines.insert(1, f"**{len(notices)} 件**（" + " / ".join(f"{k} {n}" for k, n in kinds.most_common()) + f"）。日付の読めないもの {undated} 件")
    text = "\n".join(lines)
    with open(os.path.join(OUT, "report.md"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    gh = os.environ.get("GITHUB_STEP_SUMMARY")
    if gh:
        with open(gh, "a", encoding="utf-8") as f:
            f.write("\n" + text + "\n")


if __name__ == "__main__":
    main()
