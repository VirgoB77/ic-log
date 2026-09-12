#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""保存したページから、届出の1件1件を取り出す。

recon.py が残した data/raw/<id>/<日付>.html を読んで、
data/parsed/<id>/<日付>.json に書き出す。

取り出すもの
  条文       … 第5条第1項＝新設、第6条＝変更、など。種類の手がかりになる
  届出年月日
  店舗名称
  縦覧期間   … いつまで公開されるか。これを過ぎると元ページから消える
  資料        … PDFなどへのリンク

県ごとにページの作りが違うので、県ごとに読み方を書く。
いまは兵庫県と神戸市の2つ。増やすときは EXTRACTORS に足す。

Python 3 の標準ライブラリだけで動く。
"""

import glob
import hashlib
import html
import json
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xlsx import _serial_to_date as serial_to_date  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
OUT = os.path.join(HERE, "data", "parsed")


# ---------------------------------------------------------------- 下ごしらえ

def text_of(fragment):
    """タグを落として、ふつうの文字列にする。"""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def tables_with_context(page):
    """表を、その直前の見出しとセットで取り出す。

    兵庫県は「第6条第1項」という見出しの下に表を置いているので、
    見出しを覚えておかないと、新設なのか変更なのか分からなくなる。
    """
    out = []
    heading = ""
    pattern = r"<(h[1-4])\b[^>]*>(.*?)</\1>|<table\b(.*?)</table>"
    for m in re.finditer(pattern, page, re.S | re.I):
        if m.group(1):
            t = text_of(m.group(2))
            if t:
                heading = t
        else:
            out.append((heading, m.group(3)))
    return out


def rows_of(table_html, base_url):
    """表を「セルの文字列の並び」と「その行にあったリンク」に分ける。"""
    rows = []
    for tr in re.findall(r"<tr\b.*?</tr>", table_html, re.S | re.I):
        cells, links = [], []
        for c in re.findall(r"<t[dh]\b.*?</t[dh]>", tr, re.S | re.I):
            cells.append(text_of(c))
            for href in re.findall(r'href=["\']([^"\']+)["\']', c, re.I):
                links.append(urllib.parse.urljoin(base_url, html.unescape(href)))
        if any(cells):
            rows.append((cells, links))
    return rows


# ---------------------------------------------------------------- 日付を直す

ERA = {"令和": 2018, "平成": 1988, "昭和": 1925}


def to_iso(s):
    """「令和8年4月23日」も「2026年7月27日」も 2026-04-23 の形にする。"""
    if not s:
        return None
    s = s.replace("元年", "1年")
    s = re.sub(r"(令和|平成|昭和)\s*(\d{1,2})\s*[（(]\d{4}[)）]\s*年", r"\1\2年", s)   # 令和8(2026)年 → 令和8年
    m = re.search(r"(令和|平成|昭和)\s*(\d{1,2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", s)
    if m:
        y = ERA[m.group(1)] + int(m.group(2))
        return f"{y:04d}-{int(m.group(3)):02d}-{int(m.group(4)):02d}"
    m = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", s)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.search(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", s)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    # 「R1.5.30」「H30.4.1」のように頭文字で略した和暦（大阪市のExcelにある）
    m = re.search(r"\b([RHS])\s*(\d{1,2})[.．](\d{1,2})[.．](\d{1,2})", s)
    if m:
        base = {"R": 2018, "H": 1988, "S": 1925}[m.group(1)]
        return f"{base + int(m.group(2)):04d}-{int(m.group(3)):02d}-{int(m.group(4)):02d}"
    return None


def span_of(s):
    """「令和8年5月12日～ 令和8年9月14日」から始まりと終わりを取る。"""
    if not s:
        return None, None
    parts = re.split(r"～|~|から", s, maxsplit=1)
    a = to_iso(parts[0])
    b = to_iso(parts[1]) if len(parts) > 1 else None
    return a, b


def coerce_date_column(rows, threshold=0.6):
    """列ごとに「ここは日付の列」と判断して、はみ出したセルを揃える。

    役所のExcelは同じ列でも手打ちのブレがあり、日付書式のセルと、
    ただの数字（Excelの連番）と、「令和元年６月30日」という文字列が混ざる。

      グルメシティ瓢箪山店 | … | 43901      | 43916
      ブリスモール瓢箪山店 | … | 44251      | 令和元年６月30日
      イオン東大阪店      | … | 2021-04-27 | 2021-03-31

    その列の中身の多くが日付なら、残りも日付として読み直す。
    多くが日付でない列（店舗面積など）は数字のまま触らない。
    """
    if not rows:
        return rows
    width = max(len(r) for r in rows)
    out = [list(r) + [""] * (width - len(r)) for r in rows]

    for col in range(width):
        vals = [(i, out[i][col]) for i in range(len(out)) if out[i][col]]
        if len(vals) < 3:
            continue
        already = sum(1 for _, v in vals if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v))
        if already / len(vals) < threshold:
            continue                      # 日付の列ではない
        for i, v in vals:
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
                continue
            fixed = to_iso(v)             # 「令和元年６月30日」など
            if not fixed and re.fullmatch(r"\d{5}(\.\d+)?", v):
                fixed = serial_to_date(v)  # Excelの連番のまま残ったもの
            if fixed:
                out[i][col] = fixed
    return out


# ---------------------------------------------------------------- 見分ける

# 条文と、それが何の届出かの対応。
#
# 先頭から見ることが大事。「第6条第2項（附則第5条第1項）」のような書き方があり、
# 途中の「第5条」を拾うと変更を新設と読み違える。
#
#   第5条第1項  … 新設。新しい大型店ができる
#   第6条第5項  … 廃止。店舗面積が1000平米以下になる＝大型店でなくなる
#   第6条その他 … 変更。面積・営業時間・駐車場などの変更
#   第11条第3項 … 承継。設置者（建物の持ち主）が変わった
ARTICLE_MEANS = [
    (r"^中規模", "中規模"),
    (r"^附則", "変更"),                 # 附則第5条第1項＝法施行前からある店（既存店）の変更届
    (r"^法?\s*第\s*6\s*条\s*第\s*5\s*項", "廃止"),
    (r"^法?\s*第\s*5\s*条", "新設"),
    (r"^法?\s*第\s*6\s*条", "変更"),
    (r"^法?\s*第\s*8\s*条", "意見・勧告"),
    (r"^法?\s*第\s*11\s*条", "承継"),
]

# 届出ではない表（意見書など）はここで弾く
NOT_A_NOTICE = re.compile(r"意見書|市の意見|県の意見|公表")


# 「法第6条第5項」「6条5項関係」「附則5条1項」のどれでも拾う
ARTICLE_IN_TEXT = re.compile(r"(附則)?\s*第?\s*(\d+)\s*条\s*(?:第?\s*(\d+)\s*項)?")
# 条文が書いていないとき、言葉から決める（上から順に見る）
ARTICLE_BY_WORD = [
    (r"中規模", "中規模"),
    (r"承継", "第11条第3項"),
    (r"廃止", "第6条第5項"),
    (r"既存店|附則", "附則第5条第1項"),
    (r"新設|^大規模小売店舗届出書$", "第5条第1項"),   # 「大規模小売店舗届出書」は新設のときの様式名
    (r"配置|運営方法|6条2項", "第6条第2項"),
    (r"名称|代表者|小売業者|6条1項|変更", "第6条第1項"),
]

# 堺市はページの場所（URL）で種類が分かる
SLUG_ARTICLE = [
    (r"shinsetsu", "第5条第1項"), (r"haishi", "第6条第5項"), (r"shokei", "第11条第3項"),
    (r"haichi", "第6条第2項"), (r"meisho", "第6条第1項"), (r"kizon|fusoku", "附則第5条第1項"),
]


def article_in(text, allow_words=True):
    """「令和7年度 廃止の届出（法第6条第5項関係）について」→「第6条第5項」
    「新設の届出（5条1項関係）」→「第5条第1項」
    「届出状況について」→ 空（条文が書いていない）
    """
    text = text or ""
    if re.search(r"中規模", text):
        return "中規模"
    m = ARTICLE_IN_TEXT.search(text)
    if m and m.group(2) in ("5", "6", "8", "11"):
        art = f"第{m.group(2)}条"
        if m.group(3):
            art += f"第{m.group(3)}項"
        if m.group(1):
            art = "附則" + art
        return art
    if allow_words:
        for pat, art in ARTICLE_BY_WORD:
            if re.search(pat, text):
                return art
    return ""


def means_of(article):
    article = article.strip()
    for pat, name in ARTICLE_MEANS:
        if re.search(pat, article):
            return name
    return "不明"


def norm_head(c):
    """「住 民 等 意 見」「店舗名称 （所在地）」→ 空白・記号を落として比べる。"""
    return re.sub(r"[\s（）()・、．.]", "", c or "")


# 列名のゆれ → こちらの項目名。上から順に、最初に当たったものを使う。
# 兵庫県・神戸市・堺市・岸和田市の見出しを全部ここで受ける。
HTML_COLS = [
    ("kind_col",    r"^(区分|届出の種類|届出書類名|届出区分)$"),
    ("date",        r"^(届出年月日|届出日|受理日)$"),
    ("store",       r"^(店舗名称|店舗の名称|届出の名称|大規模小売店舗の名称|建物名称|名称)"),
    ("address",     r"^(店舗の所在地|所在地)$"),
    ("operator",    r"^(設置者|設置する者|建物設置者|設置者名|旧設置者)$"),
    ("new_operator", r"^新設置者$"),
    ("event_on",    r"^(新設日|変更日|廃止日|承継日|開店日|新設する日)$"),
    ("content",     r"^(変更事項|変更内容|届出内容|届出概要|概要)$"),
    ("span",        r"縦覧"),
    ("meeting",     r"^説明会"),
    ("citizen_opinion", r"^(住民等意見|住民意見|住民等の意見)"),
    ("city_opinion", r"^(市意見|府意見|県意見)"),
    ("note",        r"^(備考|市留意事項)$"),
]


def map_columns(header):
    """見出し行から、どの列が何かを当てる。"""
    heads = [norm_head(c) for c in header]
    idx = {}
    for field, pat in HTML_COLS:
        for i, hd in enumerate(heads):
            if hd and re.search(pat, hd) and i not in idx.values():
                idx[field] = i
                break
    return idx


def split_store(cell):
    """「コジマNEW堺店 （堺区大仙西町6丁184番地1）」→ 店名と所在地に分ける。

    堺市は1つのセルに両方入れている。岸和田市は「告示文 [PDFファイル／62KB」の
    ような添付の名残がつくので、それも落とす。
    """
    t = re.sub(r"\s*(告示文|縦覧資料|届出書)?\s*\[PDF[^\]]*\]?.*$", "", cell).strip()
    t = re.sub(r"\s+\d+条\d+項届出.*$", "", t).strip()
    # 「(仮称)コープ野々井店 (南区野々井…)」のように店名の頭にも括弧があるので、
    # 最初の括弧ではなく、いちばん後ろの「所在地らしい括弧」で切る
    m = re.match(r"^(.*)[（(]([^（()）]*(?:区|市|町|丁目|番)[^（()）]*)[)）]?\s*$", t)
    if m and m.group(1).strip():
        return m.group(1).strip(), m.group(2).strip()
    return t, ""


# ---------------------------------------------------------------- 読み取る

def extract_generic(page, base_url, how, hint=""):
    """HTMLの表から届出を1件ずつ取り出す。

    how が "heading" なら直前の見出しから条文を取り、"firstrow" なら
    表の1行目の最初のセルから取る（神戸市がこの形）。
    hint はページのURLなど。堺市は年度別ページのURLに種類が入っている。
    """
    found = []
    for heading, table in tables_with_context(page):
        rows = rows_of(table, base_url)
        if len(rows) < 2:
            continue

        if NOT_A_NOTICE.search(heading):
            continue

        # 阪南市：1件が「項目名 | 値」の縦長の表。横に倒して1行にする
        if all(len(c) == 2 for c, _ in rows) and len(rows) >= 4:
            labels = [c[0] for c, _ in rows]
            if any(re.search(r"店舗|名称", l) for l in labels) and any("届出" in l for l in labels):
                links = [u for _, ls in rows for u in ls]
                rows = [([l for l in labels], []), ([c[1] for c, _ in rows], links)]

        if how == "firstrow" and len(rows[0][0]) <= 2:
            article = article_in(rows[0][0][0]) or rows[0][0][0]
            rows = rows[1:]
        else:
            article = article_in(heading, allow_words=False)
            if not article:
                for pat, art in SLUG_ARTICLE:
                    if re.search(pat, hint):
                        article = art
                        break
            if not article and "chukibo" in hint:
                article = "中規模"
        if not rows:
            continue

        idx = map_columns(rows[0][0])
        if "store" not in idx or "date" not in idx:
            continue
        # 見出しに条文が無く、行にも区分が無いときだけ、見出しの言葉から推定する
        heading_article = article or ("" if "kind_col" in idx else article_in(heading))

        for cells, links in rows[1:]:
            def cell(k):
                i = idx.get(k)
                return cells[i] if i is not None and i < len(cells) else ""

            store, addr_in_name = split_store(cell("store"))
            if not store or norm_head(store) in ("店舗名称", "店舗の名称", "届出の名称", "届出なし", "なし"):
                continue
            d = to_iso(cell("date"))
            if not d:
                continue
            # 行ごとの区分（松原市「新設」、門真市「法第5条第1項」、熊取町「変更届出書」）
            article = heading_article
            if "kind_col" in idx and cell("kind_col"):
                article = article_in(cell("kind_col")) or article
            # 阪南市のように、どこにも種類が書いていないページがある。
            # 店名と届出日がある以上は届出なので、種類不明のまま残す（捨てない）
            a, b = span_of(cell("span"))
            rec = {
                "article": article,
                "kind": means_of(article) if article else "不明",
                "notified_on": d,
                "notified_raw": cell("date"),
                "store": store,
                "address": cell("address") or addr_in_name,
                "operator": cell("operator"),
                "new_operator": cell("new_operator"),
                "event_on": to_iso(cell("event_on")),
                "content": cell("content"),
                "review_from": a,
                "review_to": b,
                "meeting": cell("meeting"),
                "citizen_opinion": cell("citizen_opinion"),
                "city_opinion": cell("city_opinion"),
                "note": cell("note"),
                "docs": [u for u in links if re.search(r"\.(pdf|xlsx?|docx?)$", u, re.I)],
            }
            found.append(rec)
    return found


EXTRACTORS = {
    "hyogo-pref-juran": dict(base="https://web.pref.hyogo.lg.jp/ks21/wd24_000000018.html", how="heading"),
    "kobe-city": dict(base="https://www.city.kobe.lg.jp/a31812/business/sangyoshinko/shokogyo/koritenporitchi/daitenhp/index.html", how="firstrow"),
    "sakai-city": dict(base="https://www.city.sakai.lg.jp/sangyo/shienyuushi/kojoricchi/daikibo/todokede/index.html", how="heading"),
    "kishiwada-city": dict(base="https://www.city.kishiwada.lg.jp/page/43-daitentodokede.html", how="heading"),
    # ここから下は 2026-09-12 に足した移譲市町村と中規模。列名の対応表でどれだけ通るか見る
    "toyonaka-city": dict(base="https://www.city.toyonaka.osaka.jp/machi/sangyoushinkou/kigyoricchi/daikibokouritenpo/todokede.html", how="heading"),
    "minoh-city": dict(base="https://www.city.minoh.lg.jp/syoukou/daikibominoh.html", how="heading"),
    "hirakata-city": dict(base="https://www.city.hirakata.osaka.jp/0000003373.html", how="heading"),
    "ibaraki-city": dict(base="https://www.city.ibaraki.osaka.jp/kikou/sangyo/shoukou/menu/daikibotyukibokouritenpo/tensyutsu/48906.html", how="heading"),
    "matsubara-city": dict(base="https://www.city.matsubara.lg.jp/docs/page3041.html", how="heading"),
    "sennan-city": dict(base="https://www.city.sennan.lg.jp/kakuka/shiminseikatu/sangyoushinkou/shokorodokakari/town/daikibo/todokede/12417.html", how="heading"),
    "kadoma-city": dict(base="https://www.city.kadoma.osaka.jp/soshiki/shiminbunkabu/6/3/4/2484.html", how="heading"),
    "kumatori-town": dict(base="https://www.town.kumatori.lg.jp/soshiki/sangyo_shinko/gyomu/sangyo_shinko/shokogyo/2357.html", how="heading"),
    "hannan-city": dict(base="https://www.city.hannan.lg.jp/kakuka/mirai/kikaku/daikibokouritennporittihou/index.html", how="heading"),
    "yao-city": dict(base="https://www.city.yao.osaka.jp/sangyou_business/sangyoushinkou_kigyoushien/1012001/1012008/index.html", how="heading"),
    "sakai-chukibo": dict(base="https://www.city.sakai.lg.jp/sangyo/shienyuushi/kojoricchi/chukouritenpo/chukiboichiran.html", how="heading"),
    "yao-chukibo": dict(base="https://www.city.yao.osaka.jp/sangyou_business/sangyoushinkou_kigyoushien/1012001/1012003.html", how="heading"),
    "minoh-2shi2cho": dict(base="https://www.city.minoh.lg.jp/syoukou/daikibo.html", how="heading"),
}


def make_key(source, rec):
    """同じ届出を日をまたいで同じものと見なすための目印。

    これがあるから「今日から消えた＝縦覧が終わった」が分かる。
    店舗名と届出日が変わらないかぎり同じ目印になる。
    """
    seed = f"{source}|{rec['article']}|{rec['notified_on']}|{rec['store']}|{rec.get('address','')}"
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]


def parse_file(source, path):
    conf = EXTRACTORS[source]
    with open(path, encoding="utf-8", errors="replace") as f:
        page = f.read()
    recs = extract_generic(page, conf["base"], conf["how"], hint=os.path.basename(path))
    for r in recs:
        r["source"] = source
        r["key"] = make_key(source, r)
    return recs


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    total = 0
    summary = []

    for source in sorted(EXTRACTORS):
        if only and only != source:
            continue
        # 同じ日の保存ページ（入口と、そこから辿った先）をまとめて1つにする。
        # 堺市は入口が目次で、中身は年度別ページに散らばっている
        by_day = {}
        for path in sorted(glob.glob(os.path.join(RAW, source, "*.html"))):
            day = os.path.basename(path)[:10]
            by_day.setdefault(day, []).append(path)
        for day, paths in sorted(by_day.items()):
            recs, seen = [], set()
            for path in paths:
                for r in parse_file(source, path):
                    if r["key"] in seen:          # 入口と年度別ページに同じ表が出ることがある
                        continue
                    seen.add(r["key"])
                    recs.append(r)
            d = os.path.join(OUT, source)
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, f"{day}.json"), "w", encoding="utf-8") as f:
                json.dump(recs, f, ensure_ascii=False, indent=1)
            kinds = {}
            for r in recs:
                kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
            summary.append((source, day, len(recs), kinds))
            total += len(recs)

    print(f"# 取り出した結果（合計 {total} 件）\n")
    for source, day, n, kinds in summary:
        k = " / ".join(f"{a} {b}件" for a, b in sorted(kinds.items(), key=lambda x: -x[1]))
        print(f"- {source} {day}: **{n}件**（{k}）")

    gh = os.environ.get("GITHUB_STEP_SUMMARY")
    if gh:
        with open(gh, "a", encoding="utf-8") as f:
            f.write(f"\n## 取り出し結果: 合計 {total} 件\n")
            for source, day, n, kinds in summary:
                f.write(f"- {source} {day}: {n}件\n")


if __name__ == "__main__":
    main()
