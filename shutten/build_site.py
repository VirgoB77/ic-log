#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data/all.json から、見せるページを作る。

1つのHTMLで全部を描くJSのアプリにはしない。検索に拾われるには、店ごと・
市区町村ごとに独立したページが要る。ここで静的なHTMLを1件ずつ書き出す。

出力（すべて shutten/ の下、GitHub Pages でそのまま配信される）
  index.html        … 入口。これから起きる予定・最近の廃止・最近の新設・市区町村と種類の一覧・検索
  a/<市区町村>.html  … その市区町村の届出一覧
  k/<種類>.html      … 種類別（新設・廃止・承継・変更・中規模）
  s/<key>.html       … 届出1件の詳細。全項目と出典
  search.json       … 入口の検索で使う軽い索引
  sitemap.xml / robots.txt

外部のCSSやJSは読まない（1ファイルで完結させる作りに合わせる）。
"""

import html
import json
import os
import re
from collections import Counter, defaultdict
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ALL = os.path.join(HERE, "data", "all.json")
SOURCES = os.path.join(HERE, "sources.json")
BASE = "/ic-log/shutten/"          # GitHub Pages のプロジェクトサイトの置き場所
SITE_NAME = "大型店日報"   # ドメインは ogataten-nippo.com の予定。「出店ウォッチ」は既存メディアと同名で使えない
CONTACT_URL = ""   # 訂正・削除の依頼フォーム（Googleフォームなど）のURL。決まったらここに入れる
REPO_ISSUES = "https://github.com/VirgoB77/ic-log/issues/new"
DISCLAIMER = "届出時点の内容です。届出のあとに変更や取下げがあることがあり、実際の開店日・閉店日と異なる場合があります。"
TAGLINE = "大阪・兵庫の大型店の開店・閉店を、届出が出た日に。"

KIND_ORDER = ["新設", "廃止", "承継", "変更", "中規模", "不明", "意見・勧告"]
KIND_COLOR = {"新設": "#1a7f37", "廃止": "#b42318", "承継": "#6e40c9", "変更": "#4b5563",
              "中規模": "#0e7490", "不明": "#6b7280", "意見・勧告": "#92400e"}
KIND_DESC = {
    "新設": "新しく大型店（店舗面積1,000㎡超）ができる届出。開店の8か月以上前に出る。",
    "廃止": "店舗面積が1,000㎡以下になる届出。大型店でなくなる＝閉店・縮小・建て替え。",
    "承継": "建物の設置者（持ち主）が変わった届出。売買や合併で出る。",
    "変更": "店名・小売業者・営業時間・駐車場などの変更届出。",
    "中規模": "1,000㎡以下の店について、市が独自に求めている届出。",
    "不明": "ページに種類が書かれていなかった届出。",
    "意見・勧告": "市が意見や勧告を出した記録。",
}


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def jp_date(s):
    if not s or len(s) < 10:
        return s or ""
    y, m, d = s[:4], int(s[5:7]), int(s[8:10])
    return f"{y}年{m}月{d}日"


def fmt_area(v):
    if v in (None, "", 0):
        return ""
    try:
        return f"{int(round(float(v))):,}㎡"
    except (TypeError, ValueError):
        return str(v)


def slug(s):
    return re.sub(r"[\\/:*?\"<>|\s]", "_", s)


# ---------------------------------------------------------------- 骨組み

CSS = """
:root{--bg:#faf9f6;--card:#fff;--ink:#1f2328;--sub:#59636e;--rule:#e5e2db;--key:#1a5cff;--soft:#f1efe9}
@media (prefers-color-scheme:dark){:root{--bg:#141517;--card:#1d1f23;--ink:#e8e6e1;--sub:#a1a7b0;--rule:#2e3138;--key:#7aa2ff;--soft:#24272d}}
*{box-sizing:border-box}html{color-scheme:light dark}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.7 -apple-system,"Hiragino Sans","Noto Sans JP","Yu Gothic UI",Meiryo,sans-serif;padding:0 16px 48px}
a{color:var(--key);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:880px;margin:0 auto}
header.top{padding:20px 0 8px;border-bottom:1px solid var(--rule);margin-bottom:20px}
header.top .name{font-weight:700;font-size:15px;letter-spacing:.02em}
header.top .name a{color:var(--ink)}
header.top .tag{color:var(--sub);font-size:13px;margin-top:2px}
h1{font-size:24px;line-height:1.35;margin:8px 0 6px}
h2{font-size:17px;margin:32px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--rule)}
.lead{color:var(--sub);font-size:14px;margin:0 0 14px}
.badge{display:inline-block;font-size:12px;font-weight:700;color:#fff;padding:1px 8px;border-radius:999px;vertical-align:middle;line-height:1.6;white-space:nowrap}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:left;padding:8px 6px;border-bottom:1px solid var(--rule);vertical-align:top}
th{color:var(--sub);font-weight:600;font-size:12px;white-space:nowrap}
td.n{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
td.d{white-space:nowrap;color:var(--sub);font-size:13px}
.list{list-style:none;padding:0;margin:0}
.list li{padding:10px 0;border-bottom:1px solid var(--rule);overflow-wrap:anywhere}
.list .m{color:var(--sub);font-size:13px;margin-top:2px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}
.chips a{background:var(--soft);color:var(--ink);padding:4px 12px;border-radius:999px;font-size:14px}
.chips a b{color:var(--sub);font-weight:500;margin-left:4px}
.kv{display:grid;grid-template-columns:8.5em 1fr;gap:6px 12px;font-size:15px}
.kv dt{color:var(--sub)}.kv dd{margin:0;overflow-wrap:anywhere}
.card{background:var(--card);border:1px solid var(--rule);border-radius:12px;padding:16px 18px;margin:12px 0}
.stat{display:flex;gap:18px;flex-wrap:wrap;margin:14px 0}
.stat div{background:var(--card);border:1px solid var(--rule);border-radius:12px;padding:10px 16px;min-width:120px}
.stat b{display:block;font-size:22px;line-height:1.2}.stat span{font-size:12px;color:var(--sub)}
.note{font-size:13px;color:var(--sub);background:var(--soft);border-radius:10px;padding:10px 14px;margin:14px 0}
footer{margin-top:44px;padding-top:16px;border-top:1px solid var(--rule);font-size:12px;color:var(--sub);line-height:1.8}
input.q{width:100%;font:inherit;padding:10px 12px;border:1px solid var(--rule);border-radius:10px;background:var(--card);color:var(--ink)}
#hits li{padding:8px 0}
@media (max-width:560px){h1{font-size:21px}.kv{grid-template-columns:1fr}.kv dt{margin-top:6px}th.hide,td.hide{display:none}}
"""


def page(title, body, rel, desc="", canonical=""):
    """共通の外枠。rel はこのページから見た shutten/ への相対パス（'' か '../'）。"""
    d = esc(desc or TAGLINE)
    can = f'<link rel="canonical" href="https://virgob77.github.io{BASE}{canonical}">' if canonical is not None else ""
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{d}">
{can}
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{d}">
<meta property="og:type" content="website">
<style>{CSS}</style>
</head>
<body><div class="wrap">
<header class="top"><div class="name"><a href="{rel}index.html">{esc(SITE_NAME)}</a></div><div class="tag">{esc(TAGLINE)}</div></header>
{body}
<footer>
<p>出典：各自治体が大規模小売店舗立地法に基づいて公告・縦覧している届出（大阪府・大阪市・堺市・兵庫県・神戸市と、大阪府から権限移譲を受けた市町）。各届出ページに出典のURLと取得日を載せています。
毎朝1回とりに行き、自治体のページから消えた届出もこのサイトには残しています。</p>
<p>{esc(DISCLAIMER)} 写し間違いもありえます。正確な内容は各届出ページの「出典」から自治体のページをご確認ください。</p>
<p><a href="{rel}about.html">このサイトについて・出典と利用規約</a> ／ <a href="{rel}contact.html">訂正・削除のご依頼</a></p>
</footer>
</div></body></html>"""


def badge(kind):
    return f'<span class="badge" style="background:{KIND_COLOR.get(kind, "#6b7280")}">{esc(kind)}</span>'


def row_link(r, rel, show_area=True):
    when = r.get("event_on") or r.get("planned_on") or ""
    area = f'<td class="hide">{esc(r["area"])}</td>' if show_area else ""
    return (f'<tr><td class="d">{esc(r["notified_on"])}</td><td>{badge(r["kind"])}</td>'
            f'<td><a href="{rel}s/{r["key"]}.html">{esc(r["store"])}</a></td>{area}'
            f'<td class="d hide">{esc(when)}</td><td class="n">{fmt_area(r.get("area_m2"))}</td></tr>')


def table(rows, rel, show_area=True, limit=None):
    head = "<tr><th>届出日</th><th>種類</th><th>店舗</th>" + ("<th class=\"hide\">市区町村</th>" if show_area else "") + "<th class=\"hide\">予定日</th><th>面積</th></tr>"
    body = "".join(row_link(r, rel, show_area) for r in (rows[:limit] if limit else rows))
    return f"<table>{head}{body}</table>"


# ---------------------------------------------------------------- 各ページ

def detail_page(r, by_ref, src_meta):
    rel = "../"
    kv = []

    def add(k, v):
        if v not in (None, "", [], 0):
            kv.append(f"<dt>{esc(k)}</dt><dd>{v}</dd>")

    add("種類", badge(r["kind"]) + (f' <span style="color:var(--sub);font-size:13px">{esc(r.get("article",""))}</span>' if r.get("article") else ""))
    add("届出日", esc(jp_date(r["notified_on"])))
    ev = r.get("event_on") or r.get("planned_on")
    if ev:
        label = {"新設": "開店予定日", "廃止": "廃止日", "承継": "承継日", "変更": "変更日"}.get(r["kind"], "予定日")
        add(label, esc(jp_date(ev)))
    if r.get("opened_on"):
        add("開店日", esc(jp_date(r["opened_on"])))
    add("所在地", esc(r.get("address") or r.get("area")))
    add("店舗面積", esc(fmt_area(r.get("area_m2"))))
    add("延床面積", esc(fmt_area(r.get("floor_area_m2"))))
    add("設置者", esc(r.get("operator")))
    add("新設置者", esc(r.get("new_operator")))
    add("小売業者", esc(r.get("retailer")))
    add("内容", esc(r.get("content")))
    if r.get("parking") or r.get("bicycle"):
        add("駐車・駐輪", esc(f"{r.get('parking') or '–'}台 / {r.get('bicycle') or '–'}台"))
    if r.get("open_time") or r.get("close_time"):
        add("営業時間", esc(f"{r.get('open_time') or ''}〜{r.get('close_time') or ''}"))
    add("用途地域", esc(r.get("zoning")))
    add("説明会", esc(r.get("meeting")))
    add("住民等の意見", esc(r.get("citizen_opinion")))
    add("市の意見", esc(r.get("city_opinion") or r.get("pref_opinion")))
    add("勧告", esc(r.get("city_recommendation") or r.get("recommendation")))
    add("備考", esc(r.get("note")))
    if r.get("review_from") or r.get("review_to"):
        add("縦覧期間", esc(f"{jp_date(r.get('review_from'))}〜{jp_date(r.get('review_to'))}"))

    hist = ""
    if r.get("history"):
        links = []
        for h in r["history"]:
            t = by_ref.get(h)
            if t and t["key"] != r["key"]:
                links.append(f'<li><a href="{t["key"]}.html">{esc(t["notified_on"])} {badge(t["kind"])} {esc(t.get("content") or t["store"])}</a></li>')
            elif t is None and h not in ("既存店",):
                links.append(f"<li>{esc(h)}</li>")
        if links:
            hist = f"<h2>同じ店の届出の流れ</h2><ul class=\"list\">{''.join(links)}</ul>"

    src_ids = r.get("sources") or [r["source"]]
    src_items = []
    for i in src_ids:
        m = src_meta.get(i, {})
        got = r.get("last_seen") or r.get("first_seen") or ""
        first = r.get("first_seen") or ""
        when = f"{got}取得" + (f"、最初に確認した日 {first}" if first and first != got else "")
        if m.get("url"):
            line = (f'出典：「{esc(m["name"])}」（<a href="{esc(m["url"])}">{esc(m["url"])}</a>、{esc(when)}）を加工して作成')
        else:
            line = f"出典：{esc(i)}（{esc(when)}）"
        sub = []
        if m.get("license"):
            sub.append(f'ライセンス：{esc(m["license"])}')
        if m.get("terms"):
            sub.append(f'利用規約：<a href="{esc(m["terms"])}">{esc(m.get("terms_name") or m["terms"])}</a>')
        src_items.append(f"<li>{line}" + (f'<div class="m">{" ／ ".join(sub)}</div>' if sub else "") + "</li>")
    src_block = '<ul class="list" style="font-size:14px">' + "".join(src_items) + "</ul>"
    status = ""
    if r.get("mode") == "snapshot":
        status = ("いまも自治体のページに載っています" if r.get("listed") else
                  f"自治体のページには載らなくなりました（最後に確認した日 {esc(r.get('last_seen'))}）")
        status = f'<p class="note">{status}。このサイトには残しています。</p>'
    ocr_note = ""
    if r.get("from_ocr"):
        names = {"address": "所在地", "operator": "設置者", "content": "内容", "area_m2": "店舗面積"}
        ocr_note = ('<p class="note">' + "・".join(names.get(k, k) for k in r["from_ocr"]) +
                    "は、自治体の資料（紙をスキャンしたPDF）を文字認識で読み取ったものです。読み違いがありえます。</p>")
    docs = ""
    if r.get("docs"):
        docs = "<h2>自治体の資料</h2><ul class=\"list\">" + "".join(
            f'<li><a href="{esc(u)}">{esc(u.rsplit("/",1)[-1])}</a></li>' for u in r["docs"][:8]) + "</ul>"

    title = f"{r['store']}（{r['area']}）の{r['kind']}届出 {jp_date(r['notified_on'])}"
    desc = f"{r['area']}の{r['store']}について、{jp_date(r['notified_on'])}に大規模小売店舗立地法の{r['kind']}届出。"
    if r.get("area_m2"):
        desc += f" 店舗面積{fmt_area(r['area_m2'])}。"
    if ev:
        desc += f" {jp_date(ev)}予定。"
    body = f"""
<p class="lead"><a href="{rel}a/{esc(slug(r['area']))}.html">{esc(r['area'])}</a> › <a href="{rel}k/{esc(r['kind'])}.html">{esc(r['kind'])}</a></p>
<h1>{esc(r['store'])}</h1>
<div class="card"><dl class="kv">{''.join(kv)}</dl></div>
<p class="note">{esc(DISCLAIMER)} 内容に誤りがある場合は<a href="{rel}contact.html">訂正・削除のご依頼</a>からお知らせください。</p>
{status}
{ocr_note}
{hist}
{docs}
<h2>出典</h2>
{src_block}
<p style="font-size:13px;color:var(--sub)">出典の書き方は各自治体の利用規約に合わせています（<a href="{rel}about.html">出典と利用規約</a>）。</p>
"""
    return page(title, body, rel, desc, canonical=f"s/{r['key']}.html")


def area_page(area, rows):
    rel = "../"
    kinds = Counter(r["kind"] for r in rows)
    chips = "".join(f'<a href="{rel}k/{esc(k)}.html">{esc(k)}<b>{kinds[k]}</b></a>' for k in KIND_ORDER if kinds.get(k))
    rows = sorted(rows, key=lambda r: r["notified_on"], reverse=True)
    latest = rows[0]["notified_on"] if rows else ""
    body = f"""
<h1>{esc(area)}の大型店の届出</h1>
<p class="lead">{len(rows)}件。最新の届出は{esc(jp_date(latest))}。</p>
<div class="chips">{chips}</div>
{table(rows, rel, show_area=False)}
"""
    desc = f"{area}で公表された大規模小売店舗立地法の届出{len(rows)}件。新設{kinds.get('新設',0)}・廃止{kinds.get('廃止',0)}・変更{kinds.get('変更',0)}。"
    return page(f"{area}の大型店の開店・閉店届出一覧", body, rel, desc, canonical=f"a/{slug(area)}.html")


def kind_page(kind, rows):
    rel = "../"
    rows = sorted(rows, key=lambda r: r["notified_on"], reverse=True)
    areas = Counter(r["area"] for r in rows)
    chips = "".join(f'<a href="{rel}a/{esc(slug(a))}.html">{esc(a)}<b>{n}</b></a>' for a, n in areas.most_common(30))
    body = f"""
<h1>{badge(kind)} {esc(kind)}の届出</h1>
<p class="lead">{esc(KIND_DESC.get(kind,''))} 全{len(rows)}件。</p>
<div class="chips">{chips}</div>
{table(rows, rel)}
"""
    return page(f"{kind}の届出一覧（大阪・兵庫の大型店）", body, rel, f"{KIND_DESC.get(kind,'')} 大阪府・兵庫県で{len(rows)}件。", canonical=f"k/{kind}.html")


def about_page(src_meta, today):
    rel = ""
    main_ids = ["osaka-pref", "osaka-city", "sakai-city", "hyogo-pref-juran", "kobe-city"]
    rows = []
    for i in main_ids:
        m = src_meta.get(i)
        if not m:
            continue
        t = (f'<a href="{esc(m["terms"])}">{esc(m.get("terms_name") or "利用規約")}</a>' if m.get("terms") else "—")
        lic = esc(m.get("license") or "政府標準利用規約（第2.0版）相当と読んでいます。要確認")
        rows.append(f'<tr><td><a href="{esc(m["url"])}">{esc(m["name"])}</a></td><td>{t}</td><td>{lic}</td></tr>')
    cities = [m for i, m in src_meta.items()
              if m.get("enabled") and m.get("area") == "osaka" and i not in main_ids and m.get("url")]
    city_items = "".join(f'<li><a href="{esc(m["url"])}">{esc(m["name"])}</a></li>' for m in sorted(cities, key=lambda m: m["name"]))
    body = f"""
<h1>このサイトについて</h1>
<p>{esc(SITE_NAME)}は、大規模小売店舗立地法（大店立地法）にもとづいて自治体が公表している「届出」を毎朝1回とりに行き、
店舗面積1,000㎡を超える大型店の新設・変更・廃止・承継を、届出が出た日に一覧にしているサイトです。
自治体のページでは縦覧期間（4か月）が過ぎると消えてしまう届出も、このサイトには残しています。</p>
<p>対象はいま大阪府と兵庫県です。届出先は都道府県と政令指定都市で、大阪府では20の市町に届出先が移譲されているため、それぞれのページを見ています。</p>

<h2>出典と利用規約</h2>
<p>載せている内容はすべて自治体が公表している届出の一覧・資料からとったもので、このサイトで表の形・並び順・表記をそろえる加工をしています。
各届出ページに、どの自治体のどのページから、いつとったかを書いています。出典の表記は各自治体の利用規約に従い、
<b>「出典：『ページ名』（URL、取得日）を加工して作成」</b>の形にしています。</p>
<div style="overflow-x:auto"><table>
<tr><th>届出先</th><th>利用規約のページ</th><th>利用条件</th></tr>
{''.join(rows)}
</table></div>
<p style="font-size:14px">大阪市の届出一覧は <a href="https://creativecommons.org/licenses/by/4.0/deed.ja">CC BY 4.0</a> で提供されています。
このサイトでは列の選択・並べ替え・表記の統一という加工をしています。</p>
<p style="font-size:14px">大阪府から権限移譲を受けた市町の届出ページ（各市町のサイト利用規約に従います）：</p>
<ul class="list" style="font-size:14px">{city_items}</ul>

<h2>免責</h2>
<p>{esc(DISCLAIMER)} 数値や日付は自治体の公表をそのまま写していますが、写し間違いがありえます。
紙をスキャンしたPDFを文字認識で読んだ項目には、その旨を各ページに書いています。
正確な内容は、各届出ページの「出典」から自治体のページをご確認ください。このサイトの内容を利用したことによる損害について、運営者は責任を負いかねます。</p>

<h2>訂正・削除のご依頼</h2>
<p>届出をした事業者の方や関係者の方で、内容の訂正や削除を望まれる場合は、<a href="{rel}contact.html">訂正・削除のご依頼</a>をご覧ください。</p>
<p style="font-size:13px;color:var(--sub)">このページの更新日：{esc(today)}</p>
"""
    return page(f"このサイトについて・出典と利用規約｜{SITE_NAME}", body, rel,
                desc=f"{SITE_NAME}の出典、各自治体の利用規約、免責、訂正・削除のご依頼について。", canonical="about.html")


def contact_page(today):
    rel = ""
    if CONTACT_URL:
        route = f'<p><a href="{esc(CONTACT_URL)}" style="display:inline-block;background:var(--key);color:#fff;padding:10px 18px;border-radius:10px;font-weight:700">依頼フォームを開く</a></p>'
    else:
        route = ('<p class="note">専用の依頼フォームを準備しています。用意でき次第このページに載せます。'
                 f'それまでは <a href="{esc(REPO_ISSUES)}">GitHub の Issue</a>（GitHubのアカウントが必要です）でもお受けします。</p>')
    body = f"""
<h1>訂正・削除のご依頼</h1>
<p>{esc(SITE_NAME)}に載っている届出の内容について、訂正や削除のご依頼を受け付けています。
届出をした事業者の方、その代理の方、届出に名前が載っている方からのご依頼を優先して対応します。</p>

<h2>ご依頼に書いていただきたいこと</h2>
<ul class="list">
<li>対象のページのURL（このサイトの「s/」で始まるページ）</li>
<li>店舗名と届出日</li>
<li>訂正か削除か。訂正の場合は、正しい内容</li>
<li>根拠（自治体の公表と食い違っている、届出を取り下げた、公表期間が終わっている、など）</li>
<li>ご依頼者のお名前・所属と、返信先</li>
</ul>

<h2>対応のしかた</h2>
<ul class="list">
<li>内容を確認のうえ、原則として7日以内に返信します。</li>
<li>自治体の公表と食い違っている場合は、公表に合わせて直します。</li>
<li>自治体の公表そのものの訂正は、このサイトではできません。届出先の自治体窓口へお願いします。</li>
<li>削除のご依頼は、公表期間が終わった届出や、個人の氏名が含まれる場合などを中心に、個別に判断します。</li>
</ul>

<h2>送り先</h2>
{route}
<p style="font-size:13px;color:var(--sub)">このページの更新日：{esc(today)}</p>
"""
    return page(f"訂正・削除のご依頼｜{SITE_NAME}", body, rel,
                desc=f"{SITE_NAME}に載っている届出の訂正・削除のご依頼について。", canonical="contact.html")


def index_page(all_recs, today):
    rel = ""
    future = sorted([r for r in all_recs if (r.get("event_on") or r.get("planned_on") or "") > today],
                    key=lambda r: r.get("event_on") or r.get("planned_on"))
    recent_close = sorted([r for r in all_recs if r["kind"] == "廃止"], key=lambda r: r["notified_on"], reverse=True)[:12]
    recent_new = sorted([r for r in all_recs if r["kind"] == "新設"], key=lambda r: r["notified_on"], reverse=True)[:12]
    gone = sorted([r for r in all_recs if r.get("mode") == "snapshot" and not r.get("listed")],
                  key=lambda r: r.get("last_seen") or "", reverse=True)[:12]
    kinds = Counter(r["kind"] for r in all_recs)
    areas = Counter(r["area"] for r in all_recs)
    area_chips = "".join(f'<a href="a/{esc(slug(a))}.html">{esc(a)}<b>{n}</b></a>' for a, n in sorted(areas.items(), key=lambda x: -x[1]))
    kind_chips = "".join(f'<a href="k/{esc(k)}.html">{badge(k)} <b>{kinds[k]}</b></a>' for k in KIND_ORDER if kinds.get(k))
    yrs = [r["notified_on"][:4] for r in all_recs if r.get("notified_on") and r["kind"] != "中規模"]
    body = f"""
<h1>大阪・兵庫の大型店、これからの開店とこれまでの閉店</h1>
<p class="lead">大規模小売店舗立地法の届出（店舗面積1,000㎡超）を、各自治体の公表ページから毎朝あつめています。届出は開店の8か月以上前に出るので、ニュースになる前に分かります。</p>
<div class="stat"><div><b>{len(all_recs):,}</b><span>届出（{min(yrs)}〜{max(yrs)}年）</span></div><div><b>{kinds.get('新設',0)}</b><span>新設</span></div><div><b>{kinds.get('廃止',0)}</b><span>廃止</span></div><div><b>{len(areas)}</b><span>市区町村</span></div></div>
<input class="q" id="q" type="search" placeholder="店名・市区町村でさがす（例：イオン、枚方市）" autocomplete="off"><ul class="list" id="hits"></ul>

<h2>これから起きる予定（{len(future)}件）</h2>
<p class="lead">届出に書かれた開店・変更・廃止の予定日が、今日より先のもの。</p>
{table(future, rel)}

<h2>最近の廃止の届出</h2>
<p class="lead">店舗面積が1,000㎡以下になる届出。閉店・縮小・建て替えのいずれか。理由が書かれているものは各ページに。</p>
{table(recent_close, rel)}

<h2>最近の新設の届出</h2>
{table(recent_new, rel)}

{"<h2>自治体のページから消えた届出</h2><p class='lead'>縦覧期間（4か月）が終わって元のページには載らなくなったもの。ここには残ります。</p>" + table(gone, rel) if gone else ""}

<h2>市区町村から</h2>
<div class="chips">{area_chips}</div>

<h2>種類から</h2>
<div class="chips">{kind_chips}</div>

<p class="note">更新：毎朝7時ごろ（最終 {esc(today)}）。大阪府・大阪市・堺市・兵庫県・神戸市と、大阪府から事務を移譲されている市町のページが対象です。</p>
<script>
(function(){{var q=document.getElementById('q'),ul=document.getElementById('hits'),idx=null;
function norm(s){{return (s||'').toLowerCase().replace(/[\\s　]/g,'')}}
q.addEventListener('input',function(){{var v=norm(q.value);if(v.length<2){{ul.innerHTML='';return}}
if(!idx){{fetch('search.json').then(function(r){{return r.json()}}).then(function(j){{idx=j;run(v)}});return}}run(v)}});
function run(v){{var out=[];for(var i=0;i<idx.length&&out.length<30;i++){{var r=idx[i];if(norm(r.s).indexOf(v)>=0||norm(r.a).indexOf(v)>=0)out.push(r)}}
ul.innerHTML=out.map(function(r){{return '<li><a href="s/'+r.k+'.html">'+r.s+'</a><div class="m">'+r.a+' · '+r.d+' · '+r.t+'</div></li>'}}).join('')||'<li class="m">見つかりませんでした</li>'}}
}})();
</script>
"""
    return page(f"{SITE_NAME}｜大阪・兵庫の大型店の開店・閉店を届出の日に", body, rel,
                f"大阪府・兵庫県の大規模小売店舗立地法の届出{len(all_recs):,}件。これから開く店、閉まる店を、自治体の公表から毎朝あつめています。", canonical="")


# ---------------------------------------------------------------- 書き出し

def main():
    with open(ALL, encoding="utf-8") as f:
        recs = json.load(f)
    with open(SOURCES, encoding="utf-8") as f:
        src_meta = {s["id"]: s for s in json.load(f)["sources"]}
    today = date.today().isoformat()

    for d in ("a", "k", "s"):
        os.makedirs(os.path.join(HERE, d), exist_ok=True)
        for old in os.listdir(os.path.join(HERE, d)):      # 消えた市区町村などの古いページを残さない
            os.remove(os.path.join(HERE, d, old))

    by_ref = {r["ref"]: r for r in recs if r.get("ref")}
    urls = []

    for r in recs:
        with open(os.path.join(HERE, "s", f"{r['key']}.html"), "w", encoding="utf-8") as f:
            f.write(detail_page(r, by_ref, src_meta))
        urls.append(f"s/{r['key']}.html")

    by_area = defaultdict(list)
    for r in recs:
        by_area[r["area"]].append(r)
    for area, rows in by_area.items():
        with open(os.path.join(HERE, "a", f"{slug(area)}.html"), "w", encoding="utf-8") as f:
            f.write(area_page(area, rows))
        urls.append(f"a/{slug(area)}.html")

    by_kind = defaultdict(list)
    for r in recs:
        by_kind[r["kind"]].append(r)
    for kind, rows in by_kind.items():
        with open(os.path.join(HERE, "k", f"{kind}.html"), "w", encoding="utf-8") as f:
            f.write(kind_page(kind, rows))
        urls.append(f"k/{kind}.html")

    with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_page(recs, today))
    with open(os.path.join(HERE, "about.html"), "w", encoding="utf-8") as f:
        f.write(about_page(src_meta, today))
    with open(os.path.join(HERE, "contact.html"), "w", encoding="utf-8") as f:
        f.write(contact_page(today))
    urls += ["about.html", "contact.html"]

    idx = [{"k": r["key"], "s": r["store"], "a": r["area"], "d": r["notified_on"], "t": r["kind"]}
           for r in sorted(recs, key=lambda r: r["notified_on"], reverse=True)]
    with open(os.path.join(HERE, "search.json"), "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, separators=(",", ":"))

    host = "https://virgob77.github.io" + BASE
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
          f"<url><loc>{host}</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq></url>"]
    for u in urls:
        sm.append(f"<url><loc>{host}{html.escape(u)}</loc><lastmod>{today}</lastmod></url>")
    sm.append("</urlset>")
    with open(os.path.join(HERE, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(sm))
    with open(os.path.join(HERE, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nDisallow: {BASE}data/\nSitemap: {host}sitemap.xml\n")

    print(f"ページを書いた: 詳細{len(recs)} / 市区町村{len(by_area)} / 種類{len(by_kind)} / index / sitemap({len(urls)+1} URL)")


if __name__ == "__main__":
    main()
