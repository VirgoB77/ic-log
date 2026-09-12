"""むかしの届出ページを Internet Archive（Wayback Machine）から取ってきて、
recon.py が保存するのと同じ場所・同じ名前（data/raw/<id>/<YYYY-MM-DD>.html）に置く。

兵庫県の「縦覧状況」と神戸市の「届出状況等」は、いま縦覧中の届出しか載らない。
過去の届出はページから消えているが、アーカイブに月ごとの保存があれば、
そこから拾って first_seen / last_seen の付いた記録として積み直せる。

置き方の約束：
- 1か月に1つの保存だけ取る（縦覧は4か月あるので、月1回見れば取りこぼさない）
- 同じ中身（digest が同じ）の保存は飛ばす
- 1回の実行で取る本数に上限を置く。続きは次回。
- 失敗した保存は台帳（data/wayback/<id>.json）に残して、何度も叩かない
- Wayback には 3 秒あけて、名乗りは他と同じ

使い方: python3 shutten/wayback.py [source-id ...]
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
LEDGER = os.path.join(HERE, "data", "wayback")

UA = "shutten-recon/0.1 (+https://github.com/VirgoB77/ic-log)"
WAIT = 3
TIMEOUT = 40
MAX_PER_RUN = int(os.environ.get("WAYBACK_MAX", "24"))     # 全部合わせて1回にこれだけ
CDX = os.environ.get("WAYBACK_CDX", "https://web.archive.org/cdx/search/cdx")
WEB = os.environ.get("WAYBACK_WEB", "https://web.archive.org/web")


def get(url, timeout=TIMEOUT):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers


def snapshots(url):
    """月ごとに1つ、200 で返った保存の一覧 [(timestamp, digest), ...] を古い順に返す。"""
    q = urllib.parse.urlencode({
        "url": url, "output": "json", "fl": "timestamp,statuscode,digest",
        "filter": "statuscode:200", "collapse": "timestamp:6",
    })
    data, _ = get(f"{CDX}?{q}")
    rows = json.loads(data.decode("utf-8") or "[]")
    out = []
    for row in rows[1:]:                      # 1行目は見出し
        ts, status, digest = row[0], row[1], row[2]
        out.append((ts, digest))
    return out


def to_text(data, headers):
    """recon.py と同じく、文字コードを見て UTF-8 にそろえて保存する。"""
    m = re.search(r"charset=([\w-]+)", headers.get("Content-Type", "") or "", re.I)
    enc = m.group(1) if m else None
    if not enc:
        head = data[:4000].decode("ascii", errors="ignore")
        m = re.search(r'charset=["\']?([\w-]+)', head, re.I)
        enc = m.group(1) if m else "utf-8"
    enc = {"shift_jis": "cp932", "shift-jis": "cp932", "sjis": "cp932", "x-sjis": "cp932",
           "euc-jp": "euc_jp"}.get(enc.lower(), enc)
    try:
        return data.decode(enc, errors="replace")
    except LookupError:
        return data.decode("utf-8", errors="replace")


def load_ledger(sid):
    p = os.path.join(LEDGER, f"{sid}.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {"done": {}, "failed": {}, "digests": []}


def save_ledger(sid, led):
    os.makedirs(LEDGER, exist_ok=True)
    with open(os.path.join(LEDGER, f"{sid}.json"), "w", encoding="utf-8") as f:
        json.dump(led, f, ensure_ascii=False, indent=1)


def backfill(sid, urls, budget, lines):
    led = load_ledger(sid)
    d = os.path.join(RAW, sid)
    os.makedirs(d, exist_ok=True)
    have_days = {n[:10] for n in os.listdir(d) if re.match(r"\d{4}-\d{2}-\d{2}", n)}
    known = set(led["digests"])
    got = 0
    for url in urls:
        try:
            snaps = snapshots(url)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as e:
            lines.append(f"  - 保存の一覧が取れなかった {url} — {type(e).__name__}: {str(e)[:60]}")
            continue
        time.sleep(WAIT)
        lines.append(f"  - {url} … アーカイブに {len(snaps)} か月分")
        for ts, digest in snaps:
            if budget[0] <= 0:
                lines.append(f"  - 今回の上限（{MAX_PER_RUN}本）に達した。続きは次回")
                save_ledger(sid, led)
                return got
            day = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"
            if ts in led["done"] or ts in led["failed"]:
                continue
            if day in have_days:                 # その日はもう手元にある（今日の分など）
                led["done"][ts] = "手元にあった"
                continue
            if digest in known:                  # 中身が変わっていない
                led["done"][ts] = "同じ中身"
                continue
            try:
                data, headers = get(f"{WEB}/{ts}id_/{url}")
            except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
                # 404/403 は何度叩いても同じなので台帳に残す。混雑や時間切れは次回もう一度
                if isinstance(e, urllib.error.HTTPError) and e.code in (403, 404):
                    led["failed"][ts] = f"HTTP {e.code}"
                lines.append(f"  - 取れなかった {day} — {type(e).__name__}: {str(e)[:60]}")
                budget[0] -= 1
                time.sleep(WAIT)
                continue
            text = to_text(data, headers)
            with open(os.path.join(d, f"{day}.html"), "w", encoding="utf-8") as f:
                f.write(text)
            have_days.add(day)
            known.add(digest)
            led["digests"].append(digest)
            led["done"][ts] = f"{len(data):,}バイト"
            got += 1
            budget[0] -= 1
            lines.append(f"  - **{day}** を置いた（{len(data):,}バイト）")
            time.sleep(WAIT)
    save_ledger(sid, led)
    return got


def main():
    with open(os.path.join(HERE, "sources.json"), encoding="utf-8") as f:
        sources = json.load(f)["sources"]
    wanted = sys.argv[1:]
    lines = ["# アーカイブから取ってきた結果", ""]
    budget = [MAX_PER_RUN]
    total = 0
    for src in sources:
        wb = src.get("wayback")
        if not wb or not src.get("enabled"):
            continue
        if wanted and src["id"] not in wanted:
            continue
        urls = wb if isinstance(wb, list) else [src["url"]]
        lines.append(f"### {src['name']}")
        lines.append("")
        total += backfill(src["id"], urls, budget, lines)
        lines.append("")
    lines.insert(1, f"**今回置いた {total}本**（1回の上限 {MAX_PER_RUN}本）")
    text = "\n".join(lines)
    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    with open(os.path.join(HERE, "data", "wayback-report.md"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    gh = os.environ.get("GITHUB_STEP_SUMMARY")
    if gh:
        with open(gh, "a", encoding="utf-8") as f:
            f.write("\n" + text + "\n")


if __name__ == "__main__":
    main()
