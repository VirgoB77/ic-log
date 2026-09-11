#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xlsx を読む（標準ライブラリだけ）。

xlsx の正体は zip に入った XML なので、外部のライブラリを入れなくても読める。
入れるものが増えるとその分だけ壊れるので、ここは自前で持つ。

読めるもの   .xlsx
読めないもの .xls（古い形式。中身がXMLではないため、別のライブラリが要る）
"""

import datetime
import re
import zipfile
from xml.etree import ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PNS = "{http://schemas.openxmlformats.org/package/2006/relationships}"

# 日付として扱う組み込みの書式番号（14〜22が日付・時刻、45〜47が経過時間）
BUILTIN_DATE = set(range(14, 23)) | set(range(45, 48))


def _shared_strings(z):
    try:
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    out = []
    for si in root.findall(f"{NS}si"):
        # <si> の下に <t> が散らばることがあるので全部つなぐ
        out.append("".join(t.text or "" for t in si.iter(f"{NS}t")))
    return out


def _date_styles(z):
    """「この書式番号は日付」という一覧を作る。

    数値のセルが日付かどうかは、セル自身ではなく書式を見ないと分からない。
    """
    try:
        root = ET.fromstring(z.read("xl/styles.xml"))
    except KeyError:
        return set()
    custom = {}
    for nf in root.iter(f"{NS}numFmt"):
        fid = int(nf.get("numFmtId", "0"))
        code = nf.get("formatCode", "")
        # 書式に y/m/d が入っていれば日付とみなす（"yyyy年m月d日" など）
        if re.search(r"[yYmMdD]", re.sub(r"\[[^\]]*\]|\"[^\"]*\"", "", code)):
            custom[fid] = True
    date_styles = set()
    xfs = root.find(f"{NS}cellXfs")
    if xfs is None:
        return date_styles
    for i, xf in enumerate(xfs.findall(f"{NS}xf")):
        fid = int(xf.get("numFmtId", "0"))
        if fid in BUILTIN_DATE or custom.get(fid):
            date_styles.add(i)
    return date_styles


def _serial_to_date(n):
    """Excel の連番を日付に直す。

    Excel は 1900年をうるう年だと思っている（実在しない1900/2/29がある）ので、
    起点を 1899-12-30 にすると 60 より大きい値がそのまま合う。
    """
    try:
        n = float(n)
    except (TypeError, ValueError):
        return None
    if n < 1:
        return None
    try:
        d = datetime.date(1899, 12, 30) + datetime.timedelta(days=int(n))
    except (OverflowError, ValueError):
        return None
    return d.isoformat()


def _col_index(ref):
    """"C7" のような番地から、0から数えた列番号を出す。"""
    m = re.match(r"([A-Z]+)", ref or "")
    if not m:
        return None
    n = 0
    for ch in m.group(1):
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def _sheet_paths(z):
    """シート名と、その中身が入っているファイルの場所を組にして返す。"""
    try:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    except KeyError:
        # 決まった場所に無ければ、シートらしきものを順に拾う
        return [(p.rsplit("/", 1)[-1], p) for p in sorted(z.namelist())
                if re.match(r"xl/worksheets/sheet\d+\.xml$", p)]
    target = {r.get("Id"): r.get("Target") for r in rels.findall(f"{PNS}Relationship")}
    out = []
    for sh in wb.iter(f"{NS}sheet"):
        t = target.get(sh.get(f"{RNS}id"), "")
        if not t:
            continue
        path = t[1:] if t.startswith("/") else ("xl/" + t.lstrip("./"))
        out.append((sh.get("name", "?"), path))
    return out


def read(path, max_rows=100000):
    """{シート名: 行の一覧} を返す。行はセルの文字列の並び。"""
    sheets = {}
    with zipfile.ZipFile(path) as z:
        shared = _shared_strings(z)
        dstyles = _date_styles(z)
        for name, sp in _sheet_paths(z):
            try:
                root = ET.fromstring(z.read(sp))
            except KeyError:
                continue
            rows = []
            for row in root.iter(f"{NS}row"):
                cells, width = {}, 0
                for c in row.findall(f"{NS}c"):
                    i = _col_index(c.get("r"))
                    if i is None:
                        i = width
                    t = c.get("t")
                    v = c.find(f"{NS}v")
                    if t == "inlineStr":
                        is_ = c.find(f"{NS}is")
                        val = "".join(x.text or "" for x in is_.iter(f"{NS}t")) if is_ is not None else ""
                    elif t == "s":
                        k = int(v.text) if v is not None and v.text else -1
                        val = shared[k] if 0 <= k < len(shared) else ""
                    else:
                        val = v.text if v is not None else ""
                        # 数値でも、書式が日付なら日付に直す
                        if val and c.get("s") and int(c.get("s")) in dstyles:
                            val = _serial_to_date(val) or val
                    cells[i] = (val or "").strip()
                    width = max(width, i + 1)
                rows.append([cells.get(i, "") for i in range(width)])
                if len(rows) >= max_rows:
                    break
            sheets[name] = rows
    return sheets
