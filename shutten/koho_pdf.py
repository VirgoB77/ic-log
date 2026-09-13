"""兵庫県公報の本体PDFから、大規模小売店舗立地法の公告（新設・変更・廃止）を読み取る。

koho.py が目録から拾った公告には（発行日, 公報番号）が付いている。
月別一覧 → 月ページ → 「M月D日第N号」の PDF、とたどれば本体に着く。
本体の公告は決まった形で、店舗名・所在地・設置者・小売業者・店舗面積・
新設（変更・廃止）の日・届出年月日・縦覧場所が書いてある。

置き方の約束：
- PDF そのものは git に残さない（1冊 300KB × 1,400冊 で重すぎる）。
  大店立地法の公告の部分だけ文字で data/koho/text/<日付>-<号>.txt に残す。
- 月ページは一度読んだら data/koho/months/<年-月>.json に控えて、二度取りに行かない
- 1回の実行で読む号数に上限を置く（KOHO_MAX、既定 40）。新しい号から順に。続きは次回
- 取れなかった号は台帳 data/koho/issues.json に理由を残す。404 以外は次回やり直す
- 代表者の氏名など個人の名前は取り出さない（法人名だけ）

出力：data/parsed/hyogo-koho/all.json（過去分を全部含む一覧として merge.py が読む）。
文字ファイルは毎回読み直すので、読み取りを直せば過去の分にも効く。

使い方: python3 shutten/koho_pdf.py
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parse as P  # noqa: E402

HOST = "https://web.pref.hyogo.lg.jp"
NOTICES = os.path.join(HERE, "data", "koho", "hyogo-notices.json")
INDEX_DIR = os.path.join(HERE, "data", "raw", "hyogo-koho-index")
MONTHS = os.path.join(HERE, "data", "koho", "months")
TEXTS = os.path.join(HERE, "data", "koho", "text")
LEDGER = os.path.join(HERE, "data", "koho", "issues.json")
OUT = os.path.join(HERE, "data", "parsed", "hyogo-koho")
REPORT = os.path.join(HERE, "data", "koho", "pdf-report.md")
SOURCE = "hyogo-koho"

UA = "shutten-recon/0.1 (+https://github.com/VirgoB77/ic-log)"
WAIT = 2
TIMEOUT = 60
MAX_PDF = 6 * 1024 * 1024
MAX_ISSUES = int(os.environ.get("KOHO_MAX", "40"))
FIRST_MONTH = (2007, 1)          # 月別一覧の最初のリンクが指す月

Z2H = str.maketrans("０１２３４５６７８９（）：，、．－―", "0123456789():,,.--")


def z2h(s):
    return (s or "").translate(Z2H)


def squash(s):
    return re.sub(r"[\s　]+", "", z2h(s))


def get(url, limit=MAX_PDF):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*", "Accept-Encoding": "identity"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        data = r.read(limit + 1)
    if len(data) > limit:
        raise ValueError("大きすぎる")
    return data


# ---------------------------------------------------------------- 月別一覧 → 月ページ
def month_index():
    """月別一覧の保存ページから {'2023-06': '/kk32/koho/202306.html', ...} を作る。

    年の見出しが拾いにくいので、1月から順に並んでいることを頼りに 2007年1月から数える。
    月の名前が並び順と食い違ったら、そこで止めて安全側に倒す。
    """
    files = sorted(glob.glob(os.path.join(INDEX_DIR, "*.html")))
    if not files:
        return {}
    with open(files[-1], encoding="utf-8", errors="replace") as f:
        s = f.read()
    links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>\s*([0-9０-９]{1,2})月\s*</a>', s)
    out = {}
    y, m = FIRST_MONTH
    for href, mon in links:
        if int(z2h(mon)) != m:
            break                                   # 並びが崩れた。ここまでにする
        out[f"{y:04d}-{m:02d}"] = urllib.parse.urljoin(HOST, href)
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def month_links(ym, url, lines):
    """月ページの「M月D日第N号」→ PDF の URL の対応。控えがあればそれを使う。"""
    os.makedirs(MONTHS, exist_ok=True)
    cache = os.path.join(MONTHS, f"{ym}.json")
    if os.path.exists(cache):
        with open(cache, encoding="utf-8") as f:
            return json.load(f)
    try:
        html_ = get(url, limit=2_000_000).decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as e:
        lines.append(f"  - 月ページが取れなかった {ym} — {type(e).__name__}: {str(e)[:60]}")
        return None
    time.sleep(WAIT)
    out = {}
    for href, label in re.findall(r'<a[^>]+href="([^"]+\.pdf)"[^>]*>(.*?)</a>', html_, re.S | re.I):
        lab = squash(re.sub(r"<[^>]+>", "", label))
        m = re.match(r"(\d{1,2})月(\d{1,2})日第(\d+)号", lab)
        if m:
            out[f"{int(m.group(1))}-{int(m.group(2))}-{m.group(3)}"] = urllib.parse.urljoin(HOST, href)
    with open(cache, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
    return out


# ---------------------------------------------------------------- PDF → 公告の文字
HEAD = re.compile(r"^\s*大規模小売店舗の(新設|変更|廃止)に関する届出\s*$")
LAW = re.compile(r"大規模小売店舗立地法")
NEXT_TITLE = re.compile(r"^\s{0,8}[^\s\d０-９（(○].{1,60}$")
PAGE_HEAD = re.compile(r"兵\s*庫\s*県\s*公\s*報|^\s*\d{1,3}\s*$|^\s*（\d+）\s*$")


def strip_page_furniture(text):
    """ページの上下に入る「令和５年６月20日 火曜日 兵庫県公報 第423号」とページ番号を落とす。"""
    out = []
    for ln in text.splitlines():
        if PAGE_HEAD.search(ln) and ("公" in ln or ln.strip().isdigit() or "（" in ln):
            continue
        out.append(ln)
    return out


def cut_sections(text):
    """本文から、大店立地法の公告のかたまりを切り出す。[(種類, 行のリスト), ...]"""
    lines = strip_page_furniture(text)
    starts = []
    for i, ln in enumerate(lines):
        m = HEAD.match(ln)
        if not m:
            continue
        nxt = " ".join(lines[i + 1:i + 4])
        if LAW.search(nxt):                         # 目次の行（……11）ではなく本文の見出し
            starts.append((i, m.group(1)))
    sections = []
    for n, (i, kind) in enumerate(starts):
        end = len(lines)
        # 次の公告の見出し：短い題名の行のすぐ後に「法律第…号」の引用が来る
        for j in range(i + 3, len(lines)):
            if NEXT_TITLE.match(lines[j]) and re.search(r"法律第\d+号|条例第\d+号|規則第\d+号", " ".join(lines[j + 1:j + 3])):
                end = j
                break
        if n + 1 < len(starts):
            end = min(end, starts[n + 1][0])
        sections.append((kind, lines[i:end]))
    return sections


# ---------------------------------------------------------------- 公告の文字 → 記録
ARTICLE = re.compile(r"第\s*([0-9０-９]+)\s*条\s*(?:の\s*[0-9０-９]+\s*)?第\s*([0-9０-９]+)\s*項")
DATE_LINE = re.compile(r"^\s*((?:平成|令和|昭和)\s*[0-9０-９元]+\s*年\s*[0-9０-９]+\s*月\s*[0-9０-９]+\s*日)\s*$")
ITEM = re.compile(r"^\s*([0-9０-９]{1,2})\s+(\S.*)$")


def value_after(lines, i, label):
    """「名称 ダイソーひめじ岡田店」形式なら同じ行から、無ければ次の空でない行から値を取る。"""
    ln = lines[i]
    m = re.search(rf"{label}\s+(\S.*)$", ln)
    if m:
        return m.group(1).strip()
    for j in range(i + 1, min(i + 4, len(lines))):
        if lines[j].strip():
            return lines[j].strip()
    return ""


def first_column(line):
    """「三菱ＨＣキャピタル株式会社     東京都…     久 井 大 樹」→ 最初の列だけ（住所や代表者名は捨てる）"""
    parts = re.split(r"\s{2,}", line.strip())
    return parts[0].strip() if parts else ""


def parse_section(kind, lines, issue):
    text = "\n".join(lines)
    am = ARTICLE.search(z2h(text[:400]))
    article = f"第{int(am.group(1))}条第{int(am.group(2))}項" if am else {"新設": "第5条第1項", "廃止": "第6条第5項"}.get(kind, "")
    # 番号付きの項目に切る
    items = {}
    cur = None
    for ln in lines:
        m = ITEM.match(ln)
        if m and int(z2h(m.group(1))) <= 15 and not re.match(r"^\s*[0-9０-９]+\s*[,，]", ln):
            cur = z2h(m.group(2))
            items[cur] = []
        elif cur is not None:
            items[cur].append(ln)

    def item(pat):
        for k, v in items.items():
            if re.search(pat, k):
                return k, v
        return None, []

    rec = {"article": article, "kind": kind, "source": SOURCE,
           "gazette_date": issue["date"], "gazette_no": issue["no"], "docs": [issue["url"]]}
    # 名称・所在地
    k, v = item(r"名称及び所在地")
    for i, ln in enumerate(v):
        if re.search(r"^\s*名称", ln) and "store" not in rec:
            rec["store"] = value_after(v, i, "名称")
        elif re.search(r"^\s*所在地", ln) and "address" not in rec:
            rec["address"] = re.sub(r"\s+", "", value_after(v, i, "所在地"))
    # 設置者（法人名だけ。住所・代表者名は取らない）
    k, v = item(r"設置(している|する)者")
    for i, ln in enumerate(v):
        if re.match(r"^\s*名称\s+\S", ln) and not re.search(r"名称\s+住所|代表者", ln):
            rec["operator"] = first_column(re.sub(r"^\s*名称\s+", "", ln))
            break
        if re.match(r"^\s*名称\s*$", ln) or re.search(r"名称\s+住所|名称\s+代表者", ln):
            for ln2 in v[i + 1:i + 4]:
                if ln2.strip() and not re.search(r"^\s*(住所|代表者)", ln2):
                    rec["operator"] = first_column(ln2)
                    break
            break
    # 小売業者（新設）
    k, v = item(r"小売業を行う者")
    names = []
    for i, ln in enumerate(v):
        if re.match(r"^\s*名称\s+\S", ln) and not re.search(r"名称\s+(住所|代表者)", ln):
            names.append(first_column(re.sub(r"^\s*名称\s+", "", ln)))
        elif re.search(r"名称\s+(代表者|住所)", ln) or re.match(r"^\s*名称\s*$", ln):
            for ln2 in v[i + 1:]:
                s = ln2.strip()
                if not s or re.match(r"^(住所|代表者)", s):
                    continue
                if re.match(r"^[0-9０-９]", s):
                    break
                names.append(first_column(ln2))
            break
    names = [n for n in names if n and n not in ("外未定", "ほか未定")]
    if names:
        rec["retailer"] = "、".join(dict.fromkeys(names))
    # 日付と面積
    for pat, field in ((r"新設をする日|新設する日", "event_on"), (r"変更年月日|変更をする日", "event_on"),
                       (r"以下となる日|廃止する日|廃止の日", "event_on"), (r"届出年月日", "notified_on")):
        k, v = item(pat)
        for ln in v:
            dm = DATE_LINE.match(ln)
            if dm:
                rec[field] = P.to_iso(squash(dm.group(1)))
                break
    k, v = item(r"店舗面積の合計$|店舗面積の合計（|廃止前の店舗面積")
    for ln in v:
        mm = re.search(r"([0-9０-９,，]+)\s*平方メートル", z2h(ln))
        if mm:
            rec["area_m2"] = int(mm.group(1).replace(",", ""))
            break
    if kind == "変更":
        k, v = item(r"変更事項")
        head = next((ln.strip() for ln in v if ln.strip() and not re.match(r"^\s*[(（]", ln)), "")
        rec["content"] = re.sub(r"\s+", " ", head)[:80]
    k, v = item(r"縦覧場所及び縦覧期間")
    for ln in v:
        if "県民" in ln or "土木事務所" in ln:
            pm = re.search(r"(阪神南|阪神北|東播磨|北播磨|中播磨|西播磨|但馬|丹波|淡路)", ln)
            if pm:
                rec["region"] = pm.group(1)
            break
    rec["review_from"] = issue["date"]
    if not rec.get("notified_on") or not rec.get("store"):
        return None
    rec["store"] = re.sub(r"\s+", " ", rec["store"]).strip()
    rec["key"] = P.make_key(SOURCE, rec)
    return rec


def parse_text_file(path):
    """data/koho/text の 1 ファイル（1 号ぶん）から記録を返す。"""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"(\d{4}-\d{2}-\d{2})-(\d+)\.txt$", os.path.basename(path))
    issue = {"date": m.group(1), "no": m.group(2), "url": ""}
    first = text.split("\n", 1)[0]
    if first.startswith("# "):                     # 1 行目に PDF の URL を書いてある
        issue["url"] = first[2:].strip()
    recs = []
    for kind, lines in cut_sections(text):
        r = parse_section(kind, lines, issue)
        if r:
            recs.append(r)
    return recs


# ---------------------------------------------------------------- 取りに行く
def load_ledger():
    if os.path.exists(LEDGER):
        with open(LEDGER, encoding="utf-8") as f:
            return json.load(f)
    return {}


def fetch_issue(issue, url, lines):
    """PDF を落として文字にし、大店立地法の公告の部分だけ text に残す。戻り値は公告の数。"""
    data = get(url)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        r = subprocess.run(["pdftotext", "-layout", tmp_path, "-"], capture_output=True, timeout=120)
        text = r.stdout.decode("utf-8", errors="replace")
    finally:
        os.remove(tmp_path)
    sections = cut_sections(text)
    os.makedirs(TEXTS, exist_ok=True)
    with open(os.path.join(TEXTS, f"{issue['date']}-{issue['no']}.txt"), "w", encoding="utf-8") as f:
        f.write(f"# {url}\n")
        for kind, sec in sections:
            f.write("\n".join(sec).rstrip() + "\n\n")
    return len(sections)


def main():
    lines = ["# 兵庫県公報の本体から読んだ大店立地法の公告", ""]
    fetched = 0
    if os.path.exists(NOTICES) and shutil.which("pdftotext"):
        with open(NOTICES, encoding="utf-8") as f:
            notices = json.load(f)
        issues = {}
        for n in notices:
            if n["kind"] in ("新設", "変更", "廃止") and n["date"] and n["no"].isdigit():
                issues.setdefault((n["date"], n["no"]), 0)
                issues[(n["date"], n["no"])] += 1
        ledger = load_ledger()
        index = month_index()
        lines.append(f"- 目録にある届出の公告 {sum(issues.values())} 件、号にして {len(issues)} 号。月別一覧 {len(index)} か月")
        todo = [k for k in sorted(issues, reverse=True) if f"{k[0]}#{k[1]}" not in ledger
                or (not ledger[f"{k[0]}#{k[1]}"].get("status", "").startswith("done")
                    and "404" not in ledger[f"{k[0]}#{k[1]}"].get("status", ""))]
        lines.append(f"- 未読の号 {len(todo)}。今回は新しいほうから {MAX_ISSUES} 号まで")
        for (d, no) in todo[:MAX_ISSUES]:
            key = f"{d}#{no}"
            ym = d[:7]
            murl = index.get(ym)
            if not murl:
                ledger[key] = {"status": "月ページが一覧に無い"}
                continue
            links = month_links(ym, murl, lines)
            if links is None:
                continue
            y, m, dd = d.split("-")
            url = links.get(f"{int(m)}-{int(dd)}-{no}")
            if not url:
                ledger[key] = {"status": "月ページに号が無い"}
                lines.append(f"  - {d} 第{no}号: 月ページに見つからない")
                continue
            try:
                n = fetch_issue({"date": d, "no": no}, url, lines)
                ledger[key] = {"status": "done", "url": url, "sections": n, "when": date.today().isoformat()}
                fetched += 1
                lines.append(f"  - **{d} 第{no}号** 公告 {n} 件（目録では {issues[(d, no)]} 件）")
            except urllib.error.HTTPError as e:
                ledger[key] = {"status": f"failed: HTTP {e.code}", "url": url}
                lines.append(f"  - {d} 第{no}号: HTTP {e.code}")
            except (urllib.error.URLError, OSError, ValueError, subprocess.TimeoutExpired) as e:
                ledger[key] = {"status": f"failed: {type(e).__name__}", "url": url}
                lines.append(f"  - {d} 第{no}号: {type(e).__name__}: {str(e)[:50]}")
            time.sleep(WAIT)
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "w", encoding="utf-8") as f:
            json.dump(ledger, f, ensure_ascii=False, indent=0, sort_keys=True)
    else:
        lines.append("- 目録がまだ無いか pdftotext が無いので、取りに行かなかった")

    # 手元の文字ファイルを全部読み直す
    recs, seen = [], set()
    for path in sorted(glob.glob(os.path.join(TEXTS, "*.txt"))):
        for r in parse_text_file(path):
            if r["key"] in seen:
                continue
            seen.add(r["key"])
            recs.append(r)
    recs.sort(key=lambda r: (r["notified_on"], r["store"]))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "all.json"), "w", encoding="utf-8") as f:
        json.dump(recs, f, ensure_ascii=False, indent=1)
    kinds = {}
    for r in recs:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    lines.insert(1, f"**今回読んだ {fetched} 号 / 手元の文字から {len(recs)} 件**（" + " / ".join(f"{k} {n}" for k, n in sorted(kinds.items())) + "）")
    text = "\n".join(lines)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    gh = os.environ.get("GITHUB_STEP_SUMMARY")
    if gh:
        with open(gh, "a", encoding="utf-8") as f:
            f.write("\n" + text + "\n")


if __name__ == "__main__":
    main()
