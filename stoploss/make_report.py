#!/usr/bin/env python3
"""out/results.json と out/*.png から、1ファイルで読める報告書 index.html を作る。"""
import os, json, base64
import pandas as pd
import backtest as bt

OUT = bt.OUT
HERE = bt.HERE
res = json.load(open(os.path.join(OUT, "results.json")))
sweep = pd.read_csv(os.path.join(OUT, "sweep.csv"))


def img(name):
    with open(os.path.join(OUT, name), "rb") as f:
        return f'<img src="data:image/png;base64,{base64.b64encode(f.read()).decode()}" alt="{name}">'


def pct(x, digits=3):
    if x is None:
        return "—"
    return f"{x:+.{digits}f}%"


def cls(x):
    if x is None:
        return ""
    return "pos" if x > 0 else "neg"


STRAT_LABEL = {"capit_long": "投げ売り確定型 → 買い", "capit_short": "投げ売り確定型 → 売り",
               "wick_long": "だまし型(ヒゲ) → 買い", "wick_short": "だまし型(ヒゲ) → 売り"}


def table(tf, horizons, digits):
    unit = bt.TIMEFRAMES[tf]["unit"]
    rows = []
    for sym, m in res["markets"].items():
        S = m["timeframes"][tf]["strategies"]
        for key, lab in STRAT_LABEL.items():
            for H in horizons:
                st = S[key]["horizons"][str(H)]
                if st.get("n", 0) == 0:
                    continue
                rows.append(f"<tr><td>{m['label']}</td><td>{lab}</td><td>{H}{unit}</td><td>{st['n']}</td>"
                            f"<td class='{cls(st['mean_gross_pct'])}'>{pct(st['mean_gross_pct'], digits)}</td>"
                            f"<td class='{cls(st['mean_net_pct'])}'><b>{pct(st['mean_net_pct'], digits)}</b></td>"
                            f"<td>{st['win_rate']*100:.0f}%</td>"
                            f"<td class='{cls(st['excess_pct'])}'>{pct(st['excess_pct'], digits)}</td>"
                            f"<td>{pct(st['first_half_net_pct'], digits)} / {pct(st['second_half_net_pct'], digits)}</td></tr>")
    return ("<div class='scroll'><table><thead><tr><th>相場</th><th>入り方</th><th>持つ長さ</th><th>回数</th><th>1回あたり<br>(コスト前)</th>"
            "<th>1回あたり<br>(コスト後)</th><th>勝率</th><th>合図なしとの差</th><th>前半 / 後半<br>(コスト後)</th></tr></thead><tbody>"
            + "".join(rows) + "</tbody></table></div>")


def sweep_table():
    sw = sweep[sweep.n >= 30]
    g = sw.groupby(["market", "tf", "signal", "dir"]).agg(configs=("n", "size"), pos=("mean_net_pct", lambda x: (x > 0).mean()),
                                                         med=("mean_net_pct", "median")).reset_index()
    rows = []
    for _, r in g.iterrows():
        lab = STRAT_LABEL[f"{r.signal}_{r.dir}"]
        rows.append(f"<tr><td>{bt.MARKETS[r.market]['label']}</td><td>{bt.TIMEFRAMES[r.tf]['label']}</td><td>{lab}</td>"
                    f"<td>{int(r.configs)}</td><td class='{'pos' if r.pos >= 0.7 else ('neg' if r.pos <= 0.3 else '')}'>{r.pos*100:.0f}%</td>"
                    f"<td class='{cls(r.med)}'>{pct(r.med, 3)}</td></tr>")
    return ("<div class='scroll'><table><thead><tr><th>相場</th><th>足</th><th>入り方</th><th>試した設定の数</th><th>コスト後で<br>プラスだった設定の割合</th>"
            "<th>1回あたりの中央値<br>(コスト後)</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>")


def market_list():
    rows = []
    for sym, m in res["markets"].items():
        rows.append(f"<tr><td>{m['label']}</td><td>{m['start'][:10]} 〜 {m['end'][:10]}</td><td>{m['bars_1h']:,}本</td>"
                    f"<td>{'0.10%（往復）' if sym == 'BTCUSD' else str(bt.MARKETS[sym]['cost']) + ' pips（往復）'}</td></tr>")
    return "<table><thead><tr><th>相場</th><th>期間</th><th>1時間足の本数</th><th>見込んだコスト</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"


B = res["markets"]["BTCUSD"]["timeframes"]
b1 = B["1d"]["strategies"]["capit_long"]["horizons"]["1"]
b1h = B["1h"]["strategies"]["capit_long"]["horizons"]["1"]
b1h_short = B["1h"]["strategies"]["capit_short"]["horizons"]["24"]
revisit = {sym: res["markets"][sym]["timeframes"]["1h"]["strategies"]["capit_long"]["horizons_stop"]["24"]["stopped_rate"] for sym in res["markets"]}

html = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>損切りの山の逆張り：過去データで検証</title>
<style>
 body{{font-family:-apple-system,"Hiragino Sans","Noto Sans JP",sans-serif;margin:0;background:#f7f6f2;color:#222;line-height:1.7}}
 main{{max-width:900px;margin:0 auto;padding:16px}}
 h1{{font-size:1.5em;border-left:8px solid #1a7f4b;padding-left:12px}}
 h2{{font-size:1.25em;margin-top:2em;border-bottom:2px solid #1a7f4b;padding-bottom:4px}}
 h3{{font-size:1.05em;margin-top:1.5em}}
 img{{max-width:100%;height:auto;border:1px solid #ddd;background:#fff;border-radius:6px}}
 .box{{background:#fff;border:1px solid #ddd;border-radius:8px;padding:12px 16px;margin:12px 0}}
 .verdict{{background:#e8f4ec;border-color:#1a7f4b}}
 .warn{{background:#fff4e5;border-color:#d3671d}}
 table{{border-collapse:collapse;font-size:0.85em;background:#fff}}
 th,td{{border:1px solid #ddd;padding:4px 8px;text-align:right;white-space:nowrap}}
 th{{background:#eee}} td:first-child,td:nth-child(2){{text-align:left}}
 .pos{{color:#1a7f4b}} .neg{{color:#c0392b}}
 .scroll{{overflow-x:auto}}
 dt{{font-weight:bold;margin-top:8px}} dd{{margin-left:1em}}
 code{{background:#eee;padding:1px 4px;border-radius:3px}}
 small{{color:#666}}
</style></head><body><main>
<h1>「損切りの山が出たら逆に入る」を過去データで検証した</h1>
<p><small>作った日: 2026-09-06 ／ お金は動かしていない。過去の値動きに当てはめて数えただけの結果。</small></p>

<div class="box verdict">
<h2 style="margin-top:0;border:none">結論（先に3行）</h2>
<ol>
<li><b>短い時間（1時間足で数時間〜2日）では、この考えは儲からなかった。</b> 4つの相場すべてで、コストを引くとマイナス。特にビットコインで「上に跳ねたあとに売る」は大負け。</li>
<li><b>ビットコインの日足で「投げ売りの翌日に買う」だけはプラスだった</b>（{b1['n']}回、1回あたり{pct(b1['mean_net_pct'],1)}、勝率{b1['win_rate']*100:.0f}%）。ただし回数が少なく、儲かった年は上げ相場の年に偏る。「聖杯」とは言えない。</li>
<li><b>損切りの山の安値は、そのあと7〜8割の確率でもう一度割られる。</b> 「損切りが出た＝底」ではない。反転を取るなら、底が固まるまで待つ工夫が要る。</li>
</ol>
</div>

<h2>1. 何を試したか</h2>
<p>他人の損切り注文は見えない。でも、損切りが一斉に出た足には共通の跡が残る。次の3つがそろった足を「損切りの山」とみなした。</p>
<ol>
<li><b>直近の安値（高値）を突き抜けた</b> … 損切り注文は「直近の安値のすぐ下」に置かれやすい</li>
<li><b>足の長さ（高値−安値）が、ふだんの2倍以上</b> … 注文がなだれ込んで一気に動いた</li>
<li><b>出来高（FXは値が動いた回数）が、ふだんの2倍以上</b></li>
</ol>
<p>「ふだん」は直近24本（1時間足）／20本（日足）の平均で決めた。実際の例が下の図。黄色の足が「損切りの山」。</p>
{img('examples.png')}
<p>入り方は2種類。</p>
<dl>
<dt>投げ売り確定型</dt><dd>足が安値を割ったまま終わった（黒い太い足）。次の足の始値で「買う」。反発ねらい。</dd>
<dt>だまし型（ヒゲ）</dt><dd>足の途中で安値を割ったが、終わるまでに戻した（下に長いヒゲ）。損切りだけ刈られて戻る「ストップ狩り」の形。次の足の始値で「買う」。</dd>
</dl>
<p>上に突き抜けた場合は逆に「売る」。出口は「決めた時間がたったら終値で出る」。コスト（スプレッドと手数料）を差し引いた数字も出した。</p>
<p>比べる相手は<b>「合図なしで、同じ長さだけ同じ方向に持った場合の平均」</b>。これより良くなければ、合図に意味はない。</p>
{market_list()}

<h2>2. 短い時間（1時間足）の結果</h2>
<p>合図が出たあと、平均して値がどう動いたか。緑・オレンジ・青が合図あり、灰色の点線が合図なし。<b>合図の線が点線より上にいれば、合図に意味がある。</b></p>
{img('paths_1h.png')}
<div class="box">
<p><b>読み方</b></p>
<ul>
<li>ビットコイン「下への山のあと買い」：最初の1時間だけ小さく跳ねる（平均{pct(b1h['mean_gross_pct'],2)}）。しかしコスト0.10%より小さいので、手元には残らない。そのあと1日かけてズルズル下がる。</li>
<li>ビットコイン「上への山のあと売り」：ずっと下がり続ける＝上に跳ねたあとは、さらに上がる。逆張りは大やけど（24時間持って1回あたり{pct(b1h_short['mean_net_pct'],2)}）。</li>
<li>FX3つ：線が0のまわりでふらふらしているだけ。合図なしとほぼ同じ。動きの幅が0.05%（ドル円で約7銭）しかないので、スプレッドで消える。</li>
</ul>
</div>
<p>コストを引いた損益を、全部足していった線。右肩上がりなら儲かっている。</p>
{img('equity_1h.png')}
{table('1h', [1, 4, 24], 3)}
<p><small>「前半 / 後半」は期間を半分に割ったときの1回あたり。両方ともプラスでないと信用できない。</small></p>

<h2>3. 長い時間（日足）の結果</h2>
<p>日足だと「損切りの山」は年に数回しか出ない。FXでは10年間で1〜5回しかなく、判断できなかった。ビットコインだけ{b1['n']}回あった。</p>
{img('btc_daily.png')}
<div class="box">
<p><b>読み方</b></p>
<ul>
<li>投げ売りの翌日に買って、その日の終値で売る：1回あたり{pct(b1['mean_net_pct'],2)}（コスト後）、勝率{b1['win_rate']*100:.0f}%。合図なし（毎日買っていた場合）より{pct(b1['excess_pct'],2)}良い。</li>
<li>ただし、儲かった年は 2015〜2017年・2020〜2021年・2023年以降で、いずれも上げ相場。2019年・2022年の下げ相場ではマイナス。つまり「大きな上げ相場の中の押し目を買っていた」と読むほうが正しい。</li>
<li>前半（2015〜2020）は1回あたり{pct(b1['first_half_net_pct'],1)}、後半は{pct(b1['second_half_net_pct'],1)}。効き目は弱まっている。</li>
<li>{b1['n']}回は少ない。統計の目安（t値）は{b1['t_stat']:.1f}で、「たまたま」を否定しきれないぎりぎり。</li>
</ul>
</div>
{table('1d', [1, 3, 5], 2)}

<h2>4. 「損切りの山の安値」は、そのあと割られるか</h2>
<p>「山の安値を、ふだんの足の半分ぶん下に割ったら諦めて出る」という損切りをつけて数えた。棒は、持っている間にそこまで落ちた割合。</p>
{img('stop_revisit.png')}
<div class="box warn">
<p>1時間足では約{max(revisit.values())*100:.0f}%、日足でも6割弱が、いったん反発したあと安値をまた割っている。<b>損切りの山は「底」ではなく「途中」であることのほうが多い。</b>
損切りをつけた場合の成績は、つけない場合よりさらに悪くなった（安値のすぐ上で入るので、少しの揺れで切られる）。</p>
</div>

<h2>5. 「たまたま」ではないかの確認</h2>
<p>「直近何本を見るか」「ふだんの何倍か」「何本後に出るか」を変えて、合計{len(sweep):,}通り試した。結果が設定によってころころ変わるなら、それは「たまたま」。</p>
{sweep_table()}
<p><small>回数が30回未満の設定は除いた。「プラスだった設定の割合」が70%以上なら緑、30%以下なら赤。</small></p>
<p>ビットコイン日足「投げ売り確定型→買い」だけは、どの設定でもプラス（一貫している）。1時間足はどの相場・どの設定でもほぼマイナス。ユーロドルの「だまし型→売り」とドル円の「だまし型→売り」は設定を問わずわずかにプラスだが、1回あたり0.02〜0.04%で、実際のスプレッドの揺れで消える大きさ。</p>

<h2>6. この検証の限界（正直なところ）</h2>
<ul>
<li><b>本物の損切りデータは使っていない。</b> 値動きと出来高から「損切りの山らしい足」を推定しただけ。暗号資産の取引所が出す「強制清算」の金額や、FX会社の「お客さんの買い売り比率」を使えば、もっと直接に確かめられる。ただしそれには口座（API）が要る。</li>
<li><b>FXの出来高はティック数</b>（値が動いた回数）で、本当の売買量ではない。データは1社の配信（MetaTrader系）で、2022年3月で切れている。</li>
<li>ビットコインは Bitstamp（海外取引所）のドル建て。日本の取引所は手数料・スプレッドがもっと広いことが多く、結果はさらに悪くなる。</li>
<li>すべり（注文が思った値段で通らないこと）は見込んでいない。損切りの山の直後は特にすべりやすいので、実際はもう少し悪い。</li>
<li>同時に持つのは1つだけ、資金の大きさは無視、金利・スワップも無視。</li>
</ul>

<h2>7. ここから何をするか</h2>
<ol>
<li><b>短い時間の逆張りはやめる。</b> データがはっきり「ダメ」と言っている。</li>
<li>ビットコインの日足の「投げ売り翌日に買う」を追いかけるなら、まず<b>本物のお金を使わずに、これから出る合図を記録して当たるか見る</b>（フォワードテスト）。半年〜1年分たまってから判断する。</li>
<li>「損切りの山の安値は割られる」を逆に使う：山が出てもすぐ入らず、<b>安値をもう一度試して割れなかったのを見てから</b>入る（二番底）。これは次に検証できる。</li>
<li>本物の損切り（強制清算）データで確かめたいなら、持っている取引所の名前を教えてもらえれば、そのAPIで取れるかを調べる。</li>
</ol>

<h2>8. 自分で動かすとき</h2>
<p>このフォルダに全部入っている。パソコンに Python が入っていれば、次の順に実行するだけで同じ結果が出る。</p>
<pre><code>pip install pandas numpy matplotlib
python3 backtest.py      # 計算（20秒くらい）→ out/results.json, out/sweep.csv
python3 charts.py        # グラフ → out/*.png
python3 make_report.py   # この報告書 → index.html</code></pre>
<p>元データは <code>data/</code> に1時間足で入れてある（作り直すときは <code>prepare_data.py</code>）。出どころは README に書いた。</p>
</main></body></html>
"""
with open(os.path.join(HERE, "index.html"), "w") as f:
    f.write(html)
print("wrote index.html", len(html) // 1024, "KB")
