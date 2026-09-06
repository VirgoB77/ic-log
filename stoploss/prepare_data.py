#!/usr/bin/env python3
"""元データ（GitHub 上の公開CSV）を、検証で使う「1時間足」にそろえて保存する。

  ビットコイン : Bitstamp の1分足 (ff137/bitstamp-btcusd-minute-data) を1時間足にまとめる
  FX          : komo135/forex-historical-data の1時間足をそのまま（値の桁だけ直す）

作った 1時間足は stoploss/data/*.1h.csv.gz に入る。backtest.py はこれだけを読む。

使い方:
  python3 prepare_data.py <元データを置いたフォルダ>
"""
import sys, os, gzip
import pandas as pd

SRC = sys.argv[1] if len(sys.argv) > 1 else "raw"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(OUT, exist_ok=True)


def save(df, name):
    path = os.path.join(OUT, f"{name}.1h.csv.gz")
    df = df[["open", "high", "low", "close", "volume"]].copy()
    df.index.name = "time"
    df.to_csv(path, float_format="%.6g", compression="gzip")
    print(f"{name}: {len(df):,} 本  {df.index[0]} 〜 {df.index[-1]}  -> {path}")


# ---- ビットコイン (Bitstamp 1分足 -> 1時間足) ----
parts = []
for fn in ["bitstamp_1min_2012-2025.csv.gz", "bitstamp_1min_latest.csv"]:
    p = os.path.join(SRC, fn)
    if os.path.exists(p):
        parts.append(pd.read_csv(p))
if parts:
    m = pd.concat(parts, ignore_index=True)
    m["time"] = pd.to_datetime(m["timestamp"], unit="s", utc=True).dt.tz_localize(None)
    m = m.drop_duplicates("time").set_index("time").sort_index()
    # 2015年より前は取引所が小さすぎて値が飛ぶので使わない
    m = m.loc["2015-01-01":]
    h = m.resample("1h").agg(open=("open", "first"), high=("high", "max"),
                             low=("low", "min"), close=("close", "last"),
                             volume=("volume", "sum")).dropna()
    save(h, "BTCUSD")

# ---- FX (komo135 の1時間足。値が 1000倍 / 100000倍 で入っているので戻す) ----
for sym, scale in [("USDJPY", 1000.0), ("GBPJPY", 1000.0), ("EURUSD", 100000.0)]:
    p = os.path.join(SRC, f"{sym}h1.csv")
    if not os.path.exists(p):
        continue
    f = pd.read_csv(p, parse_dates=["Date"]).rename(columns={"Date": "time", "tick_volume": "volume"})
    for c in ["open", "high", "low", "close"]:
        f[c] = f[c] / scale
    f = f.drop_duplicates("time").set_index("time").sort_index()
    save(f, sym)
