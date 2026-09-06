#!/usr/bin/env python3
"""本物の清算データと、値動きから推定した「損切りの山」を突き合わせる。

読むもの
  data/BTCUSD.1h.csv.gz                      値動き（Bitstamp）
  data/liq/binance_liq_BTCUSDT_1h.csv        Binance の清算（1時間ごと、2023〜2024/03）
  data/liq/coinglass_aggregated_liq_1h.csv   Coinglass の全取引所清算（あれば）
  data/liq/binance_metrics_BTCUSDT_1h.csv    建玉（あれば）

出すもの
  out/liq_compare.json  数字
  out/liq_*.png         グラフ

見ること
  1. 私の合図（損切りの山）が出た時間に、本物の清算はふだんの何倍あったか
  2. 本物の清算の山（上位1%の時間）のうち、私の合図が拾えていた割合
  3. 本物の清算の山のあとに買ったら（売ったら）どうだったか。合図なしと比べる
"""
import os, json
import numpy as np, pandas as pd
import backtest as bt

HERE = bt.HERE; OUT = bt.OUT; LIQ = os.path.join(HERE, "data", "liq")


def load_liq():
    """清算の1時間ごとの表を返す。列: long_usd, short_usd。複数あれば辞書で返す。"""
    srcs = {}
    p = os.path.join(LIQ, "binance_liq_BTCUSDT_1h.csv")
    if os.path.exists(p):
        d = pd.read_csv(p, parse_dates=["time"], index_col="time")
        srcs["Binance無料1h"] = pd.DataFrame({"long_usd": d.long_liq_usd, "short_usd": d.short_liq_usd})
    for tf in ["1h", "4h", "1d"]:
        p = os.path.join(LIQ, f"coinglass_aggregated_liq_{tf}.csv")
        if not os.path.exists(p):
            continue
        d = pd.read_csv(p, parse_dates=["time"], index_col="time")
        lc = [c for c in d.columns if "long" in c.lower() and "liq" in c.lower()]
        sc = [c for c in d.columns if "short" in c.lower() and "liq" in c.lower()]
        if lc and sc:
            srcs[f"Coinglass全取引所{tf}"] = pd.DataFrame({"long_usd": pd.to_numeric(d[lc[0]], errors="coerce"),
                                                          "short_usd": pd.to_numeric(d[sc[0]], errors="coerce")})
        else:
            print("Coinglass の列名が分からない:", list(d.columns))
    return srcs


def fwd_returns(df, idx, H):
    o = df.open.to_numpy(); c = df.close.to_numpy(); n = len(df)
    idx = idx[idx + H < n]
    return c[idx + H] / o[idx + 1] - 1.0


def analyze(name, liq, px, res):
    # 清算データの粗さ（1時間・4時間・1日）に値動きを合わせる
    step = pd.Series(liq.index).diff().median()
    if step >= pd.Timedelta(hours=23):
        px, N, horizons, gap, unit = bt.resample(px, "1D"), 20, [1, 2, 3, 5, 10], 3, "日"
    elif step >= pd.Timedelta(hours=4):
        px, N, horizons, gap, unit = bt.resample(px, "4h"), 30, [1, 3, 6, 12, 18], 6, "本(4時間)"
    else:
        N, horizons, gap, unit = 24, [1, 4, 12, 24, 48], 24, "時間"
    per_day = int(pd.Timedelta(days=1) / step) if step < pd.Timedelta(days=1) else 1
    liq = liq.copy(); liq.index = liq.index.floor(step)
    df = px.join(liq, how="inner").dropna(subset=["long_usd", "short_usd"])
    if len(df) < 200:
        print(f"{name}: 重なる期間が短すぎる ({len(df)} 本)"); return
    sigs, atr = bt.make_signals(df, N)
    df["tot"] = df.long_usd + df.short_usd
    base_med = df.tot.rolling(per_day * 30, min_periods=per_day * 7).median().shift(1)   # ふだん（直近30日の中央値）
    ratio = (df.tot / base_med).replace([np.inf], np.nan)
    r = {"period": [str(df.index[0]), str(df.index[-1])], "bars": int(len(df)), "bar": unit,
         "median_hourly_liq_usd": float(df.tot.median()), "mean_hourly_liq_usd": float(df.tot.mean())}
    # 1. 合図の時間の清算はふだんの何倍か
    for (sname, d), s in sigs.items():
        key = f"{sname}_{d}"
        rr = ratio[s].dropna()
        which = df.long_usd[s] if d == "long" else df.short_usd[s]
        r[f"signal_{key}"] = {"n": int(s.sum()), "liq_vs_normal_median": float(rr.median()) if len(rr) else None,
                              "share_over_3x": float((rr >= 3).mean()) if len(rr) else None,
                              "median_side_liq_usd": float(which.median()) if len(which) else None}
    # 2. 本物の清算の山（ロング清算の上位1%）を、合図がどれだけ拾えたか
    thr_long = df.long_usd.quantile(0.99); thr_short = df.short_usd.quantile(0.99)
    big_long = df.long_usd >= thr_long; big_short = df.short_usd >= thr_short
    near = lambda s: (pd.Series(s, index=df.index).rolling(3, center=True, min_periods=1).max() > 0)  # 前後1本まで許す
    r["real_long_cascade"] = {"n": int(big_long.sum()), "threshold_usd": float(thr_long),
                              "caught_by_capit_long": float((near(sigs[('capit', 'long')]) & big_long).sum() / big_long.sum()),
                              "caught_by_any_long_signal": float(((near(sigs[('capit', 'long')]) | near(sigs[('wick', 'long')])) & big_long).sum() / big_long.sum())}
    r["real_short_cascade"] = {"n": int(big_short.sum()), "threshold_usd": float(thr_short),
                               "caught_by_capit_short": float((near(sigs[('capit', 'short')]) & big_short).sum() / big_short.sum())}
    # 3. 本物の清算の山のあとに逆に入ったら
    cost = bt.MARKETS["BTCUSD"]["cost"]
    r["after_real_cascade"] = {}
    for label, mask, sgn in [("long_cascade_then_buy", big_long, 1.0), ("short_cascade_then_sell", big_short, -1.0)]:
        idx = np.flatnonzero(mask.to_numpy())
        # 連続する時間はまとめて最初の1回だけ
        idx = idx[np.concatenate([[True], np.diff(idx) > gap])]
        row = {"n": int(len(idx))}
        for H in horizons:
            fr = sgn * fwd_returns(df, idx, H)
            allr = sgn * fwd_returns(df, np.arange(len(df)), H)
            row[f"H{H}"] = {"mean_gross_pct": float(fr.mean() * 100), "mean_net_pct": float((fr.mean() - cost) * 100),
                            "win_rate": float((fr > cost).mean()), "baseline_pct": float(np.nanmean(allr) * 100),
                            "t_stat": float(fr.mean() / fr.std(ddof=1) * np.sqrt(len(fr))) if len(fr) > 2 else None}
        r["after_real_cascade"][label] = row
    # 清算の量で分けたら？（上位1%だけでなく、上位5%・10%も）
    Hq = per_day if per_day > 1 else 1   # 1日ぶん持つ
    r[f"by_quantile_long_cascade_buy_H{Hq}"] = {}
    for q in [0.90, 0.95, 0.99, 0.999]:
        m = df.long_usd >= df.long_usd.quantile(q)
        idx = np.flatnonzero(m.to_numpy()); idx = idx[np.concatenate([[True], np.diff(idx) > gap])]
        fr = fwd_returns(df, idx, Hq)
        r[f"by_quantile_long_cascade_buy_H{Hq}"][f"top{(1 - q) * 100:g}%"] = {"n": int(len(idx)), "mean_net_pct": float((fr.mean() - cost) * 100) if len(fr) else None}
    res[name] = r
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return df, sigs, big_long


def chart(name, df, sigs, big_long):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt, matplotlib.font_manager as fm
    for p in ["/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf"]:
        if os.path.exists(p): fm.fontManager.addfont(p)
    plt.rcParams.update({"font.family": "IPAPGothic", "font.size": 10, "axes.grid": True, "grid.alpha": 0.3})
    fig, axes = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True)
    axes[0].plot(df.index, df.close, color="black", lw=0.8)
    s = sigs[("capit", "long")]
    axes[0].scatter(df.index[s], df.close[s], color="#1a7f4b", s=14, label="私の合図（下への損切りの山）", zorder=3)
    axes[0].scatter(df.index[big_long], df.close[big_long], marker="x", color="#c0392b", s=30, label="本物のロング清算の山（上位1%）", zorder=4)
    axes[0].set_ylabel("ドル"); axes[0].legend(fontsize=8); axes[0].set_title(f"{name}：値動きと、私の合図・本物の清算の山", fontsize=11)
    axes[1].bar(df.index, df.long_usd / 1e6, width=0.05, color="#c0392b", label="ロング清算（百万ドル/時間）")
    axes[1].bar(df.index, -df.short_usd / 1e6, width=0.05, color="#2b5fb3", label="ショート清算")
    axes[1].legend(fontsize=8); axes[1].set_ylabel("百万ドル")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"liq_{name}.png"), dpi=110); plt.close(fig)


def main():
    px = bt.load("BTCUSD")
    srcs = load_liq()
    if not srcs:
        print("清算データがまだ無い (data/liq/)"); return
    res = {}
    for name, liq in srcs.items():
        out = analyze(name, liq, px, res)
        if out:
            chart(name, *out)
    json.dump(res, open(os.path.join(OUT, "liq_compare.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
