#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDFから文字を取り出す（標準ライブラリだけ）。

和泉市は届出状況を12年分すべてPDFで出している。河内長野市・大阪狭山市・
泉佐野市も同じ。ここが読めないと大阪の一部が丸ごと落ちる。

自治体のPDFは Identity-H という方式で、文字が「フォントの何番目の絵か」と
いう番号で入っている。そのままでは読めないが、PDFの中に「番号→文字」の
対応表（ToUnicode）が一緒に入っているので、それを使えば戻せる。

pdftotext のような外部の道具は使わない。入れるものが増えるとその分だけ壊れる。

読めないもの
  紙をスキャンしただけのPDF（文字ではなく画像なので、対応表が無い）
"""

import re
import zlib

# 文字を置く位置を動かす命令。行と列を復元するのに要る
RE_TM = re.compile(rb"([\d.+-]+)\s+([\d.+-]+)\s+([\d.+-]+)\s+([\d.+-]+)\s+"
                   rb"([\d.+-]+)\s+([\d.+-]+)\s+Tm")
RE_TD = re.compile(rb"([\d.+-]+)\s+([\d.+-]+)\s+(TD|Td)")
RE_TJ = re.compile(rb"(\[.*?\]\s*TJ|\(.*?\)\s*Tj|<[0-9A-Fa-f\s]*>\s*Tj)", re.S)
RE_HEX = re.compile(rb"<([0-9A-Fa-f\s]*)>")
RE_LIT = re.compile(rb"\((.*?)(?<!\\)\)", re.S)


def _streams(raw):
    """PDFの中の圧縮された塊を、順に展開して返す。"""
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", raw, re.S):
        body = m.group(1)
        try:
            yield zlib.decompress(body)
        except zlib.error:
            try:
                yield zlib.decompressobj().decompress(body)   # 末尾が欠けている場合
            except zlib.error:
                yield body                                    # 圧縮していない場合


def _parse_tounicode(data):
    """「番号→文字」の対応表を読む。"""
    table = {}
    for block in re.findall(rb"beginbfchar(.*?)endbfchar", data, re.S):
        for src, dst in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
            table[int(src, 16)] = _utf16(dst)
    for block in re.findall(rb"beginbfrange(.*?)endbfrange", data, re.S):
        # <lo> <hi> <始まりの文字> の形
        for lo, hi, dst in re.findall(
                rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
            lo_i, hi_i = int(lo, 16), int(hi, 16)
            base = int(dst, 16)
            if hi_i - lo_i > 65535:
                continue
            for i in range(hi_i - lo_i + 1):
                table[lo_i + i] = chr(base + i) if base + i < 0x110000 else ""
        # <lo> <hi> [<文字> <文字> …] の形
        for lo, hi, arr in re.findall(
                rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*\[(.*?)\]", block, re.S):
            lo_i = int(lo, 16)
            for i, dst in enumerate(re.findall(rb"<([0-9A-Fa-f]+)>", arr)):
                table[lo_i + i] = _utf16(dst)
    return table


def _utf16(hexbytes):
    """16進の並びを文字に直す（UTF-16BE）。"""
    try:
        b = bytes.fromhex(hexbytes.decode("ascii"))
    except ValueError:
        return ""
    if len(b) % 2:
        b += b"\x00"
    try:
        return b.decode("utf-16-be", "ignore")
    except Exception:
        return ""


def _decode_hex(hexstr, table):
    """並んだ番号を、対応表で文字に戻す。"""
    h = re.sub(rb"\s", b"", hexstr)
    if len(h) % 4:                       # 2バイト単位で読む
        h = h[:len(h) // 4 * 4]
    out = []
    for i in range(0, len(h), 4):
        try:
            cid = int(h[i:i + 4], 16)
        except ValueError:
            continue
        out.append(table.get(cid, ""))
    return "".join(out)


def _decode_literal(lit):
    """( ) で囲まれたふつうの文字列。英数字や記号に使われる。"""
    out, i = [], 0
    while i < len(lit):
        c = lit[i:i + 1]
        if c == b"\\" and i + 1 < len(lit):
            nxt = lit[i + 1:i + 2]
            out.append({b"n": b"\n", b"r": b"", b"t": b"\t"}.get(nxt, nxt))
            i += 2
        else:
            out.append(c)
            i += 1
    return b"".join(out).decode("latin1")


def extract_rows(path, y_tol=3.0):
    """PDFの文字を、行ごとにまとめて返す。

    同じ高さに置かれた文字を1行とみなし、左から右に並べ直す。
    表のPDFなら、これでだいたい行と列が戻る。
    """
    raw = open(path, "rb").read()

    table = {}
    for data in _streams(raw):
        if b"beginbfchar" in data or b"beginbfrange" in data:
            table.update(_parse_tounicode(data))

    pieces = []          # (y, x, 文字)
    for data in _streams(raw):
        if b"Tj" not in data and b"TJ" not in data:
            continue
        x = y = 0.0
        pos = 0
        while True:
            m = RE_TJ.search(data, pos)
            if not m:
                break
            # この描画命令の直前にある位置指定を拾う
            head = data[pos:m.start()]
            for mt in RE_TM.finditer(head):
                x, y = float(mt.group(5)), float(mt.group(6))
            for mt in RE_TD.finditer(head):
                x += float(mt.group(1))
                y += float(mt.group(2))

            chunk = m.group(1)
            text = "".join(_decode_hex(h, table) for h in RE_HEX.findall(chunk))
            if not text:
                text = "".join(_decode_literal(l) for l in RE_LIT.findall(chunk))
            if text.strip():
                pieces.append((y, x, text))
            pos = m.end()

    if not pieces:
        return []

    # 高さでまとめて行にする。上から下へ、左から右へ
    pieces.sort(key=lambda p: (-p[0], p[1]))
    rows, cur, cur_y = [], [], None
    for y, x, t in pieces:
        if cur_y is None or abs(y - cur_y) <= y_tol:
            cur.append((x, t))
            cur_y = y if cur_y is None else cur_y
        else:
            rows.append([t for _, t in sorted(cur)])
            cur, cur_y = [(x, t)], y
    if cur:
        rows.append([t for _, t in sorted(cur)])
    return rows


def extract_text(path):
    return "\n".join(" | ".join(r) for r in extract_rows(path))
