# 損切りの山の逆張り：過去データで検証

「含み損を抱えた人が損切りをしたら、相場は逆方向に行く」――この考えを逆手にとって
ポジションを取れば勝てるのか。過去の値動きに当てはめて数えた（バックテスト）。

- 報告書（結論・グラフ・表）: [index.html](index.html)
- 公開版: https://virgob77.github.io/ic-log/stoploss/

## 結論（短く）

1. 1時間足で数時間〜2日持つ逆張りは、ビットコイン・ドル円・ポンド円・ユーロドルのすべてで
   コストを引くとマイナス。特にビットコインで「上に跳ねたあとに売る」は大負け。
2. ビットコインの日足で「投げ売りの翌日に買う」だけはプラス（45回、1回あたり約+1.6%、勝率62%）。
   ただし儲かった年は上げ相場に偏り、回数も少ない。聖杯ではない。
3. 損切りの山の安値は、そのあと7〜8割の確率でもう一度割られる。「損切りが出た＝底」ではない。

## 考え方

他人の損切り注文は見えない。そこで「損切りが一斉に出た足」の跡を、次の3つで見つける。

1. 直近の安値（高値）を突き抜けた
2. 足の長さ（高値−安値）がふだんの2倍以上
3. 出来高（FXはティック数）がふだんの2倍以上

この足の次の始値で逆方向に入り、決めた時間がたったら終値で出る。
「投げ売り確定型（安値を割ったまま終わった足）」と「だまし型（割ったが戻したヒゲ）」の2種類、
買い・売りの両方向、持つ長さを数種類、パラメータを数百通り試した。
比べる相手は「合図なしで同じ長さ・同じ方向に持った場合の平均」。

## ファイル

| パス | 中身 |
| --- | --- |
| `index.html` | 報告書。グラフを埋め込んであり、これ1つで読める |
| `backtest.py` | 検証の本体。合図の見つけ方・売買のまね・集計 |
| `charts.py` | グラフを描く |
| `make_report.py` | `index.html` を作る |
| `prepare_data.py` | 元データを1時間足にそろえる |
| `data/*.1h.csv.gz` | 1時間足の価格データ（4相場） |
| `out/results.json` | 集計結果 |
| `out/sweep.csv` | パラメータを振った結果 |
| `out/trades_*.csv` | 1回ずつの売買の記録 |
| `out/*.png` | グラフ |

## 動かし方

```bash
pip install pandas numpy matplotlib
python3 backtest.py      # 20秒くらい
python3 charts.py
python3 make_report.py
```

グラフの日本語は IPA ゴシック（`/usr/share/fonts` にあるもの）を使う。ない環境では文字が □ になるので、
`charts.py` の先頭でフォントのパスを自分のものに変える。

## データの出どころ

すべて GitHub 上で公開されているもの。口座は使っていない。

| 相場 | 出どころ | 期間 |
| --- | --- | --- |
| ビットコイン (BTC/USD) | [ff137/bitstamp-btcusd-minute-data](https://github.com/ff137/bitstamp-btcusd-minute-data)（Bitstamp の1分足）を1時間足にまとめた | 2015-01 〜 2026-09 |
| ドル円・ポンド円・ユーロドル | [komo135/forex-historical-data](https://github.com/komo135/forex-historical-data)（1時間足、ティック数つき） | 2012-11 〜 2022-03 |

元の1分足（約340MB）はこのリポジトリに入れていない。`prepare_data.py` に元ファイルを置いたフォルダを渡すと作り直せる。

## 本物の清算データを取りに行く（GitHub Actions）

Coinglass のような清算の画面は、Claude の作業場所からは読めない。代わりに GitHub のコンピュータに
取りに行かせて、このリポジトリに CSV として置く仕組みにした。

- 手順ファイル: [.github/workflows/fetch-liquidations.yml](../.github/workflows/fetch-liquidations.yml)
- 取りに行くプログラム: `fetch_liquidations.py`
- 置き場所: `data/liq/`

取るもの（すべて無料・鍵なし）:

| ファイル | 中身 | 期間 |
| --- | --- | --- |
| `binance_liq_BTCUSDT_1h.csv` / `_1d.csv` | Binance 先物の強制清算をロング・ショート別に金額と件数でまとめたもの | Binance 側でファイルが消えていて、2026年9月時点では1日も取れなかった |
| `binance_metrics_BTCUSDT_1h.csv` | 建玉（ポジションの総量）とロングショート比率。建玉が急に減った所が清算の目印 | 2023年〜今日 |
| `recent_liq_okx.csv` | OKX の直近の清算。毎日取りに行って積み上げる | 動かし始めてから |

動かし方:

1. 手順ファイルか取りに行くプログラムが変わって送られると、自動で1回動く。
2. 手で動かすときは GitHub の画面 → **Actions** → 左の「清算データを取りに行く」 → 右の **Run workflow** →
   ブランチを選んで **Run workflow**。10〜30分で終わり、`data/liq/` にコミットが増える。
3. `main` に入れると、毎日 日本時間の朝10時にも自動で動いて積み上がる。

## Coinglass から取る（鍵が要る）

Binance の無料データは 2024年3月で止まっているので、今日までの清算は Coinglass から取る。
Coinglass の API（プログラム向けの窓口）は有料で、鍵（API キー）が要る。
鍵は GitHub の「Secrets」という金庫に入れ、取りに行く係だけが使う。チャットや
ファイルに鍵を書かないこと。

### プランと取れるもの（公式の説明書より）

| プラン | 月額 | 1分あたりの回数 | 清算の履歴で取れる細かさ | 1時間足 | 日足 |
| --- | --- | --- | --- | --- | --- |
| Hobbyist | 29ドル | 30回 | 4時間足以上（4時間足は直近180日） | 取れない | 全期間 |
| Startup | 79ドル | 80回 | 30分足以上（1時間足は直近180日） | 直近180日 | 全期間 |
| Standard | 299ドル | 300回 | 制限なし（1時間足は直近360日） | 直近360日 | 全期間 |

前回の検証でプラスが出たのは日足だったので、**Hobbyist（月29ドル）で足りる**。
1時間足の清算を何年分も取ることは、どのプランでもできない。無料プランは無い。

### 鍵を手に入れる

1. https://www.coinglass.com/ でアカウントを作ってログインする。
2. 画面上の「API」（または https://www.coinglass.com/CryptoApi ）から、プランを選んで申し込む。
   清算の履歴が取れるいちばん安いプランでよい（料金と制限は下の表）。
3. 申し込むと「API Key」という長い文字列が出る。これを控える（誰にも見せない）。

### GitHub の金庫に入れる

1. GitHub でこのリポジトリを開く → 上の **Settings**。
2. 左の **Secrets and variables** → **Actions**。
3. 緑の **New repository secret**。
4. Name に `COINGLASS_API_KEY`、Secret に控えた文字列を貼って **Add secret**。

これだけで、次に「清算データを取りに行く」が動いたときから Coinglass のぶんも取れる。
手で動かすときは Actions → 「清算データを取りに行く」 → Run workflow。

### 取るもの（`fetch_coinglass.py` の DATASETS）

| ファイル | 中身 |
| --- | --- |
| `coinglass_aggregated_liq_1d.csv` | 全取引所を合わせた BTC の清算（ロング・ショート別、日ごと、全期間） |
| `coinglass_aggregated_liq_4h.csv` | 同じものの4時間ごと（Hobbyist は直近180日） |
| `coinglass_aggregated_liq_1h.csv` | 同じものの1時間ごと（Startup 以上。Hobbyist では飛ばされる） |
| `coinglass_binance_btcusdt_liq_1d.csv` | Binance の BTCUSDT だけの清算（日ごと） |
| `coinglass_aggregated_oi_1d.csv` / `_4h.csv` | 全取引所を合わせた建玉（日ごと・4時間ごと） |
| `raw/coinglass_*_page1.json` | 返ってきた生の返事の見本（項目名を確かめる用） |
| `coinglass_state.json` | どこまで取ったか・最後のエラー |

返ってきた項目は名前を変えずに CSV に残す。プランが足りない窓口はエラーを記録して飛ばす。
回数制限（1分あたりの回数）は `COINGLASS_RPM` で控えめに決めてある。

## 検証の限界

- 本物の損切り（強制清算）データは使っていない。値動きと出来高からの推定。
- FXの出来高はティック数で、本当の売買量ではない。データは1社の配信で2022年3月まで。
- コストは往復で BTC 0.10%、ドル円 0.4pips、ポンド円 1.0pips、ユーロドル 0.4pips と置いた。
  日本の暗号資産取引所はこれより広いことが多い。すべりは見込んでいない。
- 同時に持つポジションは1つ。資金量・スワップ・金利は無視。
