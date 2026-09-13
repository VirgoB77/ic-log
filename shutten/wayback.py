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
import gzip
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
FILES = os.path.join(HERE, "data", "files")

UA = "shutten-recon/0.1 (+https://github.com/VirgoB77/ic-log)"
WAIT = 3
TIMEOUT = 90               # Wayback は混んでいると遅い。40秒では時間切れが多かった
MAX_PER_RUN = int(os.environ.get("WAYBACK_MAX", "24"))     # 全部合わせて1回にこれだけ
CDX = os.environ.get("WAYBACK_CDX", "https://web.archive.org/cdx/search/cdx")
WEB = os.environ.get("WAYBACK_WEB", "https://web.archive.org/web")


def get(url, timeout=TIMEOUT, tries=2):
    """取ってくる。Wayback は id_ 付きでも gzip のまま返すことがあるので戻す。混雑は1回だけやり直す。"""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*",
                                               "Accept-Encoding": "identity"})
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data, headers = r.read(), r.headers
            break
        except (urllib.error.URLError, OSError) as e:
            if isinstance(e, urllib.error.HTTPError) or i == tries - 1:
                raise
            time.sleep(WAIT * 3)
    if data[:2] == b"\x1f\x8b" or (headers.get("Content-Encoding") or "").lower() == "gzip":
        try:
            data = gzip.decompress(data)
        except OSError:
            pass
    return data, headers


def snapshots(url, prefix=False):
    """200 で返った保存の一覧を古い順に返す。

    ページは月ごとに1つ。前方一致（prefix=True）のときは、ファイル名が日付で変わる
    PDF（兵庫県の todokede_jyuuranYYMMDD.pdf など）を全部拾うため、中身（digest）が
    違うものを全部返す。戻り値は [(timestamp, digest, original_url), ...]
    """
    params = {"url": url, "output": "json", "fl": "timestamp,statuscode,digest,original",
              "filter": "statuscode:200"}
    if prefix:
        params.update(matchType="prefix", collapse="digest")
    else:
        params["collapse"] = "timestamp:6"
    data, _ = get(f"{CDX}?{urllib.parse.urlencode(params)}")
    rows = json.loads(data.decode("utf-8") or "[]")
    return [(row[0], row[2], row[3]) for row in rows[1:]]      # 1行目は見出し


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


def repair(sid, led, d, lines):
    """gzip のまま置いてしまった保存を消し、台帳の記録も外して、次で取り直せるようにする。"""
    bad_days = set()
    for n in sorted(os.listdir(d)):
        if not re.match(r"\d{4}-\d{2}-\d{2}\.html$", n):
            continue
        with open(os.path.join(d, n), "rb") as f:
            head = f.read(2)
        if head == b"\x1f\x8b" or head == b"\xef\xbf":   # gzip の魔法数か、それを UTF-8 化した置換文字
            os.remove(os.path.join(d, n))
            bad_days.add(n[:10])
    if bad_days:
        for ts in list(led["done"]):
            if f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}" in bad_days:
                led["done"].pop(ts)
        lines.append(f"  - 壊れていた保存 {len(bad_days)} 日分を消して取り直す対象に戻した（{', '.join(sorted(bad_days))}）")


def backfill(sid, urls, budget, lines, prefixes=()):
    led = load_ledger(sid)
    d = os.path.join(RAW, sid)
    os.makedirs(d, exist_ok=True)
    repair(sid, led, d, lines)
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
        for ts, digest, _orig in snaps:
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
    # 前方一致の PDF（縦覧一覧など）。data/files/<id>/wayback/<日付>--<名前>.pdf に置く
    fd = os.path.join(FILES, sid, "wayback")
    for pre in prefixes:
        try:
            snaps = snapshots(pre, prefix=True)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as e:
            lines.append(f"  - 前方一致の一覧が取れなかった {pre} — {type(e).__name__}: {str(e)[:60]}")
            continue
        time.sleep(WAIT)
        lines.append(f"  - {pre}* … アーカイブに {len(snaps)} 本（中身の違うもの）")
        os.makedirs(fd, exist_ok=True)
        for ts, digest, orig in snaps:
            if budget[0] <= 0:
                lines.append(f"  - 今回の上限（{MAX_PER_RUN}本）に達した。続きは次回")
                save_ledger(sid, led)
                return got
            key = f"{ts}:{digest}"
            if key in led["done"] or key in led["failed"] or digest in known:
                continue
            day = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"
            name = re.sub(r"[^\w.\-]", "_", orig.rsplit("/", 1)[-1])[:80] or "file"
            try:
                data, headers = get(f"{WEB}/{ts}id_/{orig}")
            except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
                if isinstance(e, urllib.error.HTTPError) and e.code in (403, 404):
                    led["failed"][key] = f"HTTP {e.code}"
                lines.append(f"  - 取れなかった {day} {name} — {type(e).__name__}: {str(e)[:60]}")
                budget[0] -= 1
                time.sleep(WAIT)
                continue
            with open(os.path.join(fd, f"{day}--{name}"), "wb") as f:
                f.write(data)
            known.add(digest)
            led["digests"].append(digest)
            led["done"][key] = f"{len(data):,}バイト {name}"
            got += 1
            budget[0] -= 1
            lines.append(f"  - **{day} {name}** を置いた（{len(data):,}バイト）")
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
        total += backfill(src["id"], urls, budget, lines, prefixes=src.get("wayback_prefix") or ())
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
