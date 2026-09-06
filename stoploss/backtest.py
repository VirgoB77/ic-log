#!/usr/bin/env python3
"""「損切りの山が出たら逆に入る」を過去データで検証する。

考え方（かみ砕き）
  他人の損切り注文そのものは見えない。ただ、損切りが一斉に出た足には共通の跡が残る。
    1. 直近 N 本の安値（高値）を突き抜けた   … 損切り注文は「直近の安値のすぐ下」に置かれやすい
    2. 足の長さ（高値−安値）がふだんの何倍もある … 注文がなだれ込んで一気に動いた
    3. 出来高（FXはティック数）がふだんの何倍もある
  この3つがそろった足を「損切りの山」とみなし、次の足の始値で逆方向に入る。

2種類の入り方を試す
  capit（投げ売り確定型）: 足が安値を割ったまま終わった → 次の足で買う（反発ねらい）
  wick （だまし型）      : 足の途中で安値を割ったが、終値は戻した（ヒゲ）→ 次の足で買う
  上昇側（高値を突き抜けた → 売る）も同じ考えで対称に試す。

出口は「H 本後の終値」（時間で出る）。ついでに「損切りの山の安値を割ったら諦めて出る」も試す。
コスト（スプレッド・手数料）を差し引いた数字も出す。
比べる相手（ベースライン）は「合図なしで、同じ長さだけ同じ方向に持った場合の平均」。
"""
import os, json, itertools, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

# 往復コスト。FXは pips（1pip = 0.01円 / 0.0001ドル）。BTC は割合。
MARKETS = {
    "BTCUSD": {"label": "ビットコイン(BTC/USD)", "cost_kind": "pct", "cost": 0.0010},
    "USDJPY": {"label": "ドル円(USD/JPY)",       "cost_kind": "pip", "cost": 0.4, "pip": 0.01},
    "GBPJPY": {"label": "ポンド円(GBP/JPY)",     "cost_kind": "pip", "cost": 1.0, "pip": 0.01},
    "EURUSD": {"label": "ユーロドル(EUR/USD)",   "cost_kind": "pip", "cost": 0.4, "pip": 0.0001},
}
# 時間軸ごとの設定: N=「直近何本」を見るか, horizons=何本後に出るか
TIMEFRAMES = {
    "1h": {"label": "1時間足", "rule": None,  "N": 24, "horizons": [1, 2, 4, 8, 12, 24, 48], "unit": "時間", "bar_hours": 1},
    "4h": {"label": "4時間足", "rule": "4h",  "N": 30, "horizons": [1, 2, 3, 6, 12, 18],     "unit": "本(4時間)", "bar_hours": 4},
    "1d": {"label": "日足",    "rule": "1D",  "N": 20, "horizons": [1, 2, 3, 5, 10],         "unit": "日", "bar_hours": 24},
}
K_RANGE = 2.0   # 足の長さが、ふだん(ATR)の何倍以上か
K_VOL = 2.0     # 出来高が、ふだん(中央値)の何倍以上か
SIGNALS = ["capit", "wick"]
DIRS = ["long", "short"]


def load(sym):
    df = pd.read_csv(os.path.join(DATA, f"{sym}.1h.csv.gz"), parse_dates=["time"], index_col="time")
    return df


def resample(df, rule):
    if rule is None:
        return df
    r = df.resample(rule).agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
                              close=("close", "last"), volume=("volume", "sum")).dropna()
    return r[r.volume > 0]


def cost_frac(sym, price):
    m = MARKETS[sym]
    if m["cost_kind"] == "pct":
        return np.full_like(price, m["cost"], dtype=float)
    return m["cost"] * m["pip"] / price


def make_signals(df, N, k_range=K_RANGE, k_vol=K_VOL):
    o, h, l, c, v = df.open, df.high, df.low, df.close, df.volume
    pc = c.shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    atr = tr.shift(1).rolling(N).mean()          # ふだんの足の長さ（当日を含めない）
    vol_med = v.shift(1).rolling(N).median()     # ふだんの出来高
    prior_low = l.shift(1).rolling(N).min()      # 直近N本の安値（損切りが置かれやすい所）
    prior_high = h.shift(1).rolling(N).max()
    big = ((h - l) >= k_range * atr) & (v >= k_vol * vol_med)
    sig = {
        ("capit", "long"):  big & (c < prior_low) & (c < o),
        ("capit", "short"): big & (c > prior_high) & (c > o),
        ("wick", "long"):   big & (l < prior_low) & (c >= prior_low),
        ("wick", "short"):  big & (h > prior_high) & (c <= prior_high),
    }
    return {k: s.fillna(False).to_numpy() for k, s in sig.items()}, atr.to_numpy()


STOP_BUFFER_ATR = 0.5   # 損切りの目安: 山の安値から、ふだんの足の長さの半分だけ下


def simulate(df, sig, direction, H, use_stop=False, sym=None, atr=None):
    """合図が出た足の次の足の始値で入り、H本後の終値で出る。同時に持つのは1つだけ。
    use_stop=True のときは「山の安値(高値)を、ふだんの足の半分ぶん越えたら諦めて出る」も入れる。"""
    o = df.open.to_numpy(); h = df.high.to_numpy(); l = df.low.to_numpy(); c = df.close.to_numpy()
    if atr is None:
        atr = np.zeros(len(df))
    n = len(df)
    idx = np.flatnonzero(sig)
    sgn = 1.0 if direction == "long" else -1.0
    rows = []
    last_exit = -1
    for i in idx:
        if i + H >= n or i + 1 <= last_exit:
            continue
        entry = o[i + 1]
        buf = STOP_BUFFER_ATR * (atr[i] if np.isfinite(atr[i]) else 0.0)
        stop = l[i] - buf if direction == "long" else h[i] + buf
        exit_price, exit_i, hit = c[i + H], i + H, False
        if use_stop:
            for j in range(i + 1, i + H + 1):
                if (direction == "long" and l[j] < stop) or (direction == "short" and h[j] > stop):
                    exit_price, exit_i, hit = stop, j, True
                    break
        gross = sgn * (exit_price / entry - 1.0)
        rows.append((df.index[i], df.index[i + 1], df.index[exit_i], entry, exit_price, gross, hit))
        last_exit = exit_i
    t = pd.DataFrame(rows, columns=["signal_time", "entry_time", "exit_time", "entry", "exit", "gross", "stopped"])
    if len(t):
        t["cost"] = cost_frac(sym, t.entry.to_numpy())
        t["net"] = t.gross - t.cost
    return t


def baseline(df, direction, H):
    """合図なし：どの足でも同じように入っていた場合の平均（同じ方向・同じ長さ）"""
    o = df.open.to_numpy(); c = df.close.to_numpy()
    # simulate と同じく「次の足の始値で入り、H本後の終値で出る」: 入り o[i+1], 出口 c[i+H]
    r = c[H:] / o[1:len(o) - H + 1] - 1.0 if H < len(df) - 1 else np.array([])
    sgn = 1.0 if direction == "long" else -1.0
    return float(np.nanmean(sgn * r))


def stats(t, base_mean):
    if len(t) == 0:
        return {"n": 0}
    r = t.net.to_numpy()
    eq = np.cumsum(r)
    dd = float((np.maximum.accumulate(np.concatenate([[0], eq])) - np.concatenate([[0], eq])).max())
    sd = r.std(ddof=1) if len(r) > 1 else np.nan
    half = len(t) // 2
    return {
        "n": int(len(t)),
        "mean_gross_pct": float(t.gross.mean() * 100),
        "mean_net_pct": float(r.mean() * 100),
        "median_net_pct": float(np.median(r) * 100),
        "win_rate": float((r > 0).mean()),
        "t_stat": float(r.mean() / sd * np.sqrt(len(r))) if sd and sd > 0 else 0.0,
        "total_net_pct": float(r.sum() * 100),
        "max_dd_pct": dd * 100,
        "baseline_pct": base_mean * 100,
        "excess_pct": float(t.gross.mean() * 100 - base_mean * 100),
        "first_half_net_pct": float(r[:half].mean() * 100) if half else np.nan,
        "second_half_net_pct": float(r[half:].mean() * 100) if half else np.nan,
        "stopped_rate": float(t.stopped.mean()),
    }


def avg_path(df, sig, direction, maxH):
    """合図のあとの平均的な値動き（入った値段からの%）を 1..maxH 本後まで。ベースラインも。"""
    o = df.open.to_numpy(); c = df.close.to_numpy(); n = len(df)
    sgn = 1.0 if direction == "long" else -1.0
    idx = np.flatnonzero(sig)
    idx = idx[idx + maxH < n]
    paths = np.array([[sgn * (c[i + k] / o[i + 1] - 1) for k in range(1, maxH + 1)] for i in idx]) if len(idx) else np.zeros((0, maxH))
    all_i = np.arange(0, n - maxH - 1)
    base = np.array([np.nanmean(sgn * (c[all_i + k] / o[all_i + 1] - 1)) for k in range(1, maxH + 1)])
    return (paths.mean(axis=0) * 100).tolist() if len(idx) else None, (base * 100).tolist(), int(len(idx))


def main():
    results = {"markets": {}, "config": {"K_RANGE": K_RANGE, "K_VOL": K_VOL, "timeframes": TIMEFRAMES, "markets": MARKETS}}
    sweep_rows = []
    for sym in MARKETS:
        print(f"=== {sym}")
        base_df = load(sym)
        results["markets"][sym] = {"label": MARKETS[sym]["label"], "start": str(base_df.index[0]), "end": str(base_df.index[-1]),
                                   "bars_1h": int(len(base_df)), "timeframes": {}}
        for tf, tcfg in TIMEFRAMES.items():
            df = resample(base_df, tcfg["rule"])
            N = tcfg["N"]
            sigs, atr = make_signals(df, N)
            tfres = {"bars": int(len(df)), "N": N, "strategies": {}}
            for (sname, d), s in sigs.items():
                key = f"{sname}_{d}"
                ent = {"n_signals": int(s.sum()), "horizons": {}, "horizons_stop": {}}
                for H in tcfg["horizons"]:
                    b = baseline(df, d, H)
                    t = simulate(df, s, d, H, False, sym)
                    ent["horizons"][H] = stats(t, b)
                    ts = simulate(df, s, d, H, True, sym, atr)
                    ent["horizons_stop"][H] = stats(ts, b)
                    if tf == "1h" and H == 24 or tf == "1d" and H == 3:
                        t.to_csv(os.path.join(OUT, f"trades_{sym}_{tf}_{key}_H{H}.csv"), index=False)
                maxH = max(tcfg["horizons"])
                p, bp, np_ = avg_path(df, s, d, maxH)
                ent["path"] = {"signal": p, "baseline": bp, "n": np_}
                tfres["strategies"][key] = ent
                print(f"  {tf} {key:12s} n={int(s.sum()):5d}  " + "  ".join(
                    f"H{H}:{ent['horizons'][H].get('mean_net_pct', float('nan')):+.3f}%" for H in tcfg["horizons"]))
            results["markets"][sym]["timeframes"][tf] = tfres

            # パラメータを振って、結果が「たまたま」でないかを見る
            if tf in ("1h", "1d"):
                grid_N = [12, 24, 48] if tf == "1h" else [10, 20, 40]
                grid_H = [4, 24] if tf == "1h" else [1, 3, 5]
                for N2, kr, kv in itertools.product(grid_N, [1.5, 2.0, 3.0], [1.5, 2.0, 3.0]):
                    sg, _ = make_signals(df, N2, kr, kv)
                    for (sname, d), s in sg.items():
                        for H in grid_H:
                            t = simulate(df, s, d, H, False, sym)
                            st = stats(t, baseline(df, d, H))
                            sweep_rows.append({"market": sym, "tf": tf, "signal": sname, "dir": d, "N": N2, "k_range": kr,
                                               "k_vol": kv, "H": H, **{k: st.get(k) for k in ["n", "mean_net_pct", "win_rate", "t_stat", "excess_pct"]}})
    pd.DataFrame(sweep_rows).to_csv(os.path.join(OUT, "sweep.csv"), index=False)
    with open(os.path.join(OUT, "results.json"), "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=1, default=lambda x: None if isinstance(x, float) and np.isnan(x) else float(x))
    print("saved", os.path.join(OUT, "results.json"))


if __name__ == "__main__":
    main()
