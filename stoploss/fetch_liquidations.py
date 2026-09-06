#!/usr/bin/env python3
"""清算（強制ロスカット）と建玉のデータを取りに行き、stoploss/data/liq/ にためる。

GitHub Actions（GitHub のコンピュータ）で動かす前提。手元のパソコンでも動く。

取るもの
  1. Binance 先物 BTCUSDT の強制清算の記録（1件ずつ） … 無料公開。2023年〜2024年3月末で更新が止まっている
       https://data.binance.vision/data/futures/um/daily/liquidationSnapshot/BTCUSDT/BTCUSDT-liquidationSnapshot-YYYY-MM-DD.zip
     → 1時間ごとに「ロング清算の金額」「ショート清算の金額」「件数」にまとめる
  2. Binance 先物 BTCUSDT の建玉・ロングショート比率（5分ごと） … 無料公開。今日まで続いている
       https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-YYYY-MM-DD.zip
     → 1時間ごとの終わりの値にまとめる。建玉が急に減った所＝清算の目印
  3. 直近の清算（OKX の公開窓口、鍵なし） … 毎日取りに行って積み上げる

出力（すべて小さい CSV）
  data/liq/binance_liq_BTCUSDT_1h.csv     1時間ごとの清算
  data/liq/binance_liq_BTCUSDT_1d.csv     1日ごとの清算
  data/liq/binance_metrics_BTCUSDT_1h.csv 1時間ごとの建玉など
  data/liq/recent_liq_okx.csv             OKX の直近清算（積み上げ）
  data/liq/state.json                     どこまで取ったかの覚え書き

使い方
  python3 fetch_liquidations.py [--start 2023-01-01] [--end 2026-12-31] [--skip-recent]
"""
import argparse, io, json, os, sys, time, zipfile, datetime as dt
import pandas as pd
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "liq")
os.makedirs(OUT, exist_ok=True)
STATE = os.path.join(OUT, "state.json")
BASE = "https://data.binance.vision/data/futures/um/daily"
SYMBOL = "BTCUSDT"
GIVE_UP_AFTER = 45   # 最後に取れた日から、これだけ連続で「無い」が続いたら、それ以降は無いとみなす
UA = {"User-Agent": "ic-log-stoploss/1.0 (github actions)"}


def load_state():
    if os.path.exists(STATE):
        return json.load(open(STATE))
    return {}


def save_state(st):
    json.dump(st, open(STATE, "w"), ensure_ascii=False, indent=1)


def get(url, tries=3):
    for i in range(tries):
        try:
            r = requests.get(url, timeout=60, headers=UA)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.content
        except requests.RequestException as e:
            if i == tries - 1:
                print(f"  ! {url}: {e}")
                return None
            time.sleep(2 ** (i + 1))


def read_zip_csv(content):
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        name = [n for n in z.namelist() if n.endswith(".csv")][0]
        raw = z.read(name)
    df = pd.read_csv(io.BytesIO(raw))
    # Binance の CSV は見出し行があるものと無いものが混ざっている
    if df.columns[0].isdigit() or df.columns[0].startswith("20"):
        df = pd.read_csv(io.BytesIO(raw), header=None)
    return df


def days(start, end):
    d = start
    while d <= end:
        yield d
        d += dt.timedelta(days=1)


# ---------- 1. 強制清算の記録 ----------
LIQ_COLS = ["time", "symbol", "side", "order_type", "time_in_force", "original_quantity", "price",
            "average_price", "order_status", "last_fill_quantity", "accumulated_fill_quantity"]


def liq_hourly_from_day(df):
    if df.shape[1] == len(LIQ_COLS) and not set(LIQ_COLS) <= set(df.columns):
        df.columns = LIQ_COLS
    t = pd.to_datetime(df["time"], unit="ms", utc=True).dt.tz_localize(None)
    qty = pd.to_numeric(df["accumulated_fill_quantity"], errors="coerce").fillna(
        pd.to_numeric(df["original_quantity"], errors="coerce"))
    px = pd.to_numeric(df["average_price"], errors="coerce").fillna(pd.to_numeric(df["price"], errors="coerce"))
    usd = qty * px
    # SELL の清算 = ロング（買い持ち）が飛ばされた。BUY の清算 = ショートが飛ばされた
    is_long = df["side"].astype(str).str.upper().eq("SELL")
    g = pd.DataFrame({"hour": t.dt.floor("h"), "long_usd": usd.where(is_long, 0.0), "short_usd": usd.where(~is_long, 0.0),
                      "long_n": is_long.astype(int), "short_n": (~is_long).astype(int), "usd": usd})
    h = g.groupby("hour").agg(long_liq_usd=("long_usd", "sum"), short_liq_usd=("short_usd", "sum"),
                              long_liq_count=("long_n", "sum"), short_liq_count=("short_n", "sum"),
                              max_single_usd=("usd", "max"))
    h.index.name = "time"
    return h


def fetch_binance_daily(kind, start, end, state, parse_day, out_name):
    """kind: liquidationSnapshot / metrics。日ごとの zip を取り、1時間足にまとめて追記する"""
    path = os.path.join(OUT, out_name)
    have = pd.read_csv(path, parse_dates=["time"], index_col="time") if os.path.exists(path) else None
    st = state.setdefault(kind, {"done": [], "missing": []})
    done = set(st["done"]); missing = set(st["missing"])
    last_ok = max(done) if done else None
    new = []
    consecutive_missing = 0
    for d in days(start, end):
        ds = d.isoformat()
        if ds in done:
            continue
        if ds in missing and (d < end - dt.timedelta(days=GIVE_UP_AFTER)):
            continue  # 昔の「無かった日」は取り直さない（直近だけ見直す）
        if consecutive_missing >= GIVE_UP_AFTER and (last_ok is None or ds > last_ok):
            print(f"  {kind}: {GIVE_UP_AFTER}日続けて無いので、ここで打ち切り ({ds})")
            break
        url = f"{BASE}/{kind}/{SYMBOL}/{SYMBOL}-{kind}-{ds}.zip"
        content = get(url)
        if content is None:
            missing.add(ds); consecutive_missing += 1
            continue
        try:
            new.append(parse_day(read_zip_csv(content)))
        except Exception as e:
            print(f"  ! {ds} を読めなかった: {e}")
            missing.add(ds); consecutive_missing += 1
            continue
        done.add(ds); missing.discard(ds); last_ok = max(last_ok or ds, ds); consecutive_missing = 0
        if len(done) % 30 == 0:
            print(f"  {kind}: {ds} まで {len(done)} 日")
    if new:
        add = pd.concat(new)
        have = add if have is None else pd.concat([have, add])
        have = have[~have.index.duplicated(keep="last")].sort_index()
        have.to_csv(path, float_format="%.4f")
    st["done"] = sorted(done); st["missing"] = sorted(missing)
    print(f"{kind}: 取れた日 {len(done)}, 無かった日 {len(missing)}, 今回追加 {len(new)} 日 -> {out_name}")
    return have


# ---------- 2. 建玉など（5分ごと → 1時間） ----------
MET_COLS = ["create_time", "symbol", "sum_open_interest", "sum_open_interest_value", "count_toptrader_long_short_ratio",
            "sum_toptrader_long_short_ratio", "count_long_short_ratio", "sum_taker_long_short_vol_ratio"]


def metrics_hourly_from_day(df):
    if df.shape[1] == len(MET_COLS) and not set(MET_COLS) <= set(df.columns):
        df.columns = MET_COLS
    t = pd.to_datetime(df["create_time"])
    df = df.drop(columns=["create_time", "symbol"]).apply(pd.to_numeric, errors="coerce")
    df.index = t
    h = df.resample("1h").last().dropna(how="all")
    h.index.name = "time"
    return h


# ---------- 3. 直近の清算（積み上げ） ----------
def fetch_recent():
    # OKX: 鍵なし。BTC-USDT の無期限先物（SWAP）の清算注文、直近 100 件
    try:
        r = requests.get("https://www.okx.com/api/v5/public/liquidation-orders",
                         params={"instType": "SWAP", "instFamily": "BTC-USDT", "state": "filled", "limit": "100"},
                         timeout=60, headers=UA)
        r.raise_for_status()
        rows = []
        for item in r.json().get("data", []):
            for d in item.get("details", []):
                rows.append({"time": pd.to_datetime(int(d["ts"]), unit="ms"), "side": d.get("side"), "pos_side": d.get("posSide"),
                             "price": float(d.get("bkPx", 0) or 0), "size_contracts": float(d.get("sz", 0) or 0),
                             "loss": float(d.get("bkLoss", 0) or 0)})
        append_recent("recent_liq_okx.csv", rows, ["time", "side", "price", "size_contracts"])
    except Exception as e:
        print(f"  ! OKX: {e}")
    # Bybit の窓口は GitHub のコンピュータからだと 403 で拒まれるので外した


def append_recent(name, rows, key):
    path = os.path.join(OUT, name)
    new = pd.DataFrame(rows)
    if new.empty:
        print(f"  {name}: 0 件"); return
    if os.path.exists(path):
        old = pd.read_csv(path, parse_dates=["time"])
        new = pd.concat([old, new])
    new = new.drop_duplicates(key).sort_values("time")
    new.to_csv(path, index=False)
    print(f"  {name}: 合計 {len(new)} 件 (今回 {len(rows)} 件)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2023-01-01")
    ap.add_argument("--end", default=(dt.date.today() - dt.timedelta(days=1)).isoformat())
    ap.add_argument("--skip-recent", action="store_true")
    ap.add_argument("--skip-binance", action="store_true")
    a = ap.parse_args()
    start, end = dt.date.fromisoformat(a.start), dt.date.fromisoformat(a.end)
    state = load_state()
    if not a.skip_binance:
        print("== Binance 強制清算の記録")
        h = fetch_binance_daily("liquidationSnapshot", start, end, state, liq_hourly_from_day, f"binance_liq_{SYMBOL}_1h.csv")
        save_state(state)
        if h is not None and len(h):
            d = h.resample("1D").agg(long_liq_usd=("long_liq_usd", "sum"), short_liq_usd=("short_liq_usd", "sum"),
                                     long_liq_count=("long_liq_count", "sum"), short_liq_count=("short_liq_count", "sum"),
                                     max_single_usd=("max_single_usd", "max"))
            d = d[(d.long_liq_count + d.short_liq_count) > 0]
            d.to_csv(os.path.join(OUT, f"binance_liq_{SYMBOL}_1d.csv"), float_format="%.2f")
            print(f"  期間 {h.index[0]} 〜 {h.index[-1]}、清算の合計 {(h.long_liq_usd.sum() + h.short_liq_usd.sum()) / 1e6:,.0f} 百万ドル")
        print("== Binance 建玉など")
        fetch_binance_daily("metrics", start, end, state, metrics_hourly_from_day, f"binance_metrics_{SYMBOL}_1h.csv")
        save_state(state)
    if not a.skip_recent:
        print("== 直近の清算（OKX）")
        fetch_recent()
    state["last_run"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    save_state(state)


if __name__ == "__main__":
    main()
