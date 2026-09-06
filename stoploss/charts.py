#!/usr/bin/env python3
"""backtest.py の結果をグラフにする（out/*.png）。"""
import os, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.font_manager as fm
import backtest as bt

for p in ["/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf", "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"]:
    if os.path.exists(p):
        fm.fontManager.addfont(p)
plt.rcParams.update({"font.family": "IPAPGothic", "font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 110, "savefig.dpi": 110, "axes.grid": True, "grid.alpha": 0.3})
BUY, SELL, BASE = "#1a7f4b", "#2b5fb3", "#888888"
OUT = bt.OUT
res = json.load(open(os.path.join(OUT, "results.json")))
MK = list(bt.MARKETS)


def fig_paths_1h():
    """合図のあと、平均してどう動いたか（1時間足、48時間先まで）"""
    fig, axes = plt.subplots(len(MK), 2, figsize=(10, 3.0 * len(MK)), sharex=True)
    for r, sym in enumerate(MK):
        S = res["markets"][sym]["timeframes"]["1h"]["strategies"]
        for cidx, (side, title) in enumerate([("long", "下への損切りの山のあと「買い」"), ("short", "上への損切りの山のあと「売り」")]):
            ax = axes[r][cidx]
            x = np.arange(1, 49)
            for key, lab, col, ls in [(f"capit_{side}", "投げ売り確定型", BUY if side == "long" else SELL, "-"),
                                      (f"wick_{side}", "だまし型(ヒゲ)", "#d3671d", "-")]:
                p = S[key]["path"]
                if p["signal"]:
                    ax.plot(x, p["signal"], color=col, ls=ls, lw=2, label=f"{lab}（{p['n']}回）")
            ax.plot(x, S[f"capit_{side}"]["path"]["baseline"], color=BASE, ls="--", lw=1.5, label="合図なし（ふつうに持った場合）")
            ax.axhline(0, color="black", lw=0.8)
            ax.set_title(f"{bt.MARKETS[sym]['label']}：{title}", fontsize=11)
            if cidx == 0:
                ax.set_ylabel("入った値段からの平均(%)")
            if r == len(MK) - 1:
                ax.set_xlabel("入ってからの時間")
            ax.legend(fontsize=8, loc="best")
    fig.suptitle("1時間足：損切りの山のあと、平均して値はどう動いたか（コスト差し引き前）", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    fig.savefig(os.path.join(OUT, "paths_1h.png")); plt.close(fig)


def fig_equity_1h():
    """1時間足・24時間持ち：コスト後の損益をずっと足していったらどうなるか"""
    fig, axes = plt.subplots(2, 2, figsize=(10, 6.5))
    for ax, sym in zip(axes.ravel(), MK):
        df = bt.load(sym)
        sigs, atr = bt.make_signals(df, bt.TIMEFRAMES["1h"]["N"])
        for (sname, d), s in sigs.items():
            t = bt.simulate(df, s, d, 24, False, sym)
            lab = {"capit": "投げ売り確定型", "wick": "だまし型"}[sname] + {"long": "・買い", "short": "・売り"}[d]
            col = (BUY if d == "long" else SELL)
            ax.plot(t.exit_time, t.net.cumsum() * 100, color=col, ls="-" if sname == "capit" else ":", lw=1.6, label=lab)
        ax.axhline(0, color="black", lw=0.8)
        ax.set_title(bt.MARKETS[sym]["label"], fontsize=11)
        ax.set_ylabel("損益の積み上げ(%)")
        ax.legend(fontsize=8)
        ax.tick_params(axis="x", labelsize=8)
    fig.suptitle("1時間足・24時間持ち：コストを引いた損益を全部足していった線（右肩上がりなら儲かっている）", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(os.path.join(OUT, "equity_1h.png")); plt.close(fig)


def fig_btc_daily():
    """ビットコイン日足：投げ売りの翌日に買う"""
    sym = "BTCUSD"
    df = bt.resample(bt.load(sym), "1D")
    sigs, atr = bt.make_signals(df, bt.TIMEFRAMES["1d"]["N"])
    S = res["markets"][sym]["timeframes"]["1d"]["strategies"]
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    ax = axes[0]
    x = np.arange(1, 11)
    ax.plot(x, S["capit_long"]["path"]["signal"], color=BUY, lw=2, marker="o", label=f"投げ売りの翌日に買う（{S['capit_long']['path']['n']}回）")
    ax.plot(x, S["capit_long"]["path"]["baseline"], color=BASE, ls="--", lw=1.5, label="合図なし（毎日買っていた場合）")
    ax.axhline(0, color="black", lw=0.8); ax.set_xlabel("入ってからの日数"); ax.set_ylabel("平均(%)"); ax.legend(fontsize=8)
    ax.set_title("平均してどう動いたか", fontsize=11)
    t = bt.simulate(df, sigs[("capit", "long")], "long", 1, False, sym)
    ax = axes[1]
    ax.plot(t.exit_time, t.net.cumsum() * 100, color=BUY, lw=2)
    ax.axhline(0, color="black", lw=0.8); ax.set_title("翌日に売る：損益の積み上げ(%)", fontsize=11); ax.tick_params(axis="x", labelsize=8)
    ax = axes[2]
    y = t.groupby(t.exit_time.dt.year).net.sum() * 100
    n = t.groupby(t.exit_time.dt.year).size()
    ax.bar(y.index.astype(str), y.values, color=[BUY if v >= 0 else "#c0392b" for v in y.values])
    for i, (v, k) in enumerate(zip(y.values, n.values)):
        ax.text(i, v + (0.3 if v >= 0 else -1.2), f"{k}回", ha="center", fontsize=8)
    ax.axhline(0, color="black", lw=0.8); ax.set_title("年ごとの損益(%)と回数", fontsize=11); ax.tick_params(axis="x", labelsize=8, rotation=45)
    fig.suptitle("ビットコイン日足：投げ売り（損切りの山）の翌日に買う", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(os.path.join(OUT, "btc_daily.png")); plt.close(fig)
    t.to_csv(os.path.join(OUT, "trades_BTCUSD_1d_capit_long_H1.csv"), index=False)
    return t


def candles(ax, d, sig_pos=None):
    x = np.arange(len(d))
    up = d.close >= d.open
    ax.vlines(x, d.low, d.high, color="black", lw=0.8)
    ax.bar(x[up], (d.close - d.open)[up], 0.6, bottom=d.open[up], color="white", edgecolor="black")
    ax.bar(x[~up], (d.open - d.close)[~up], 0.6, bottom=d.close[~up], color="black")
    if sig_pos is not None:
        ax.axvspan(sig_pos - 0.5, sig_pos + 0.5, color="#f5c542", alpha=0.45)
    step = max(1, len(d) // 8)
    ax.set_xticks(x[::step]); ax.set_xticklabels([str(i)[:10] for i in d.index[::step]], rotation=45, fontsize=8)


def fig_examples(t_daily):
    """実際の例：損切りの山が出た足と、そのあと"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    # 日足の例：いちばん大きく下げた投げ売りの日
    df = bt.resample(bt.load("BTCUSD"), "1D")
    sigs, atr = bt.make_signals(df, 20)
    idx = np.flatnonzero(sigs[("capit", "long")])
    drop = (df.close.to_numpy()[idx] / df.open.to_numpy()[idx] - 1)
    i = idx[np.argmin(drop)]
    w = df.iloc[i - 15:i + 16]
    candles(axes[0], w, 15)
    axes[0].set_title(f"日足の例：{str(df.index[i])[:10]} の投げ売り（黄色）とその前後", fontsize=11)
    axes[0].set_ylabel("ドル")
    # 1時間足の例：直近の投げ売り
    dh = bt.load("BTCUSD")
    sh, _ = bt.make_signals(dh, 24)
    ih = np.flatnonzero(sh[("capit", "long")])
    ih = ih[ih < len(dh) - 60][-1]
    w = dh.iloc[ih - 30:ih + 49]
    candles(axes[1], w, 30)
    axes[1].set_title(f"1時間足の例：{str(dh.index[ih])[:16]} の投げ売り（黄色）とその後2日", fontsize=11)
    fig.suptitle("ビットコイン：損切りの山（黄色の足）はこう見える。上ヒゲ下ヒゲの長い、太い黒い足", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(os.path.join(OUT, "examples.png")); plt.close(fig)


def fig_stop_revisit():
    """山の安値は、そのあと割られるか"""
    labels, vals = [], []
    for sym in MK:
        for tf, H in [("1h", "24"), ("1d", "3")]:
            st = res["markets"][sym]["timeframes"][tf]["strategies"]["capit_long"]["horizons_stop"][H]
            if st.get("n", 0) >= 20:
                labels.append(f"{bt.MARKETS[sym]['label'].split('(')[0]}\n{bt.TIMEFRAMES[tf]['label']}({st['n']}回)")
                vals.append(st["stopped_rate"] * 100)
    fig, ax = plt.subplots(figsize=(10, 3.6))
    ax.bar(labels, vals, color="#c0392b")
    for i, v in enumerate(vals):
        ax.text(i, v + 1, f"{v:.0f}%", ha="center")
    ax.set_ylim(0, 100); ax.set_ylabel("割られた割合(%)"); ax.tick_params(axis="x", labelsize=8)
    ax.set_title("下への損切りの山のあと、その安値（＋ふだんの足の半分）を、持っている間にもう一度割った割合", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "stop_revisit.png")); plt.close(fig)


if __name__ == "__main__":
    fig_paths_1h(); print("paths_1h")
    fig_equity_1h(); print("equity_1h")
    t = fig_btc_daily(); print("btc_daily")
    fig_examples(t); print("examples")
    fig_stop_revisit(); print("stop_revisit")
