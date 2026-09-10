// 実際に時間を進めながら回すループ。紙でも実弾でも同じ道を通る。
//
// 動きかた:
//   1. 出来上がった足だけを取ってくる（途中の足では判断しない）
//   2. 最後の足の終値で、持つ／持たないを決める
//   3. 今の持ち高と違えば注文を出す
//   4. 次の足が閉じるまで待つ
//
// 止めかた:
//   Ctrl-C か、bot フォルダに STOP という名前のファイルを置く。
//   STOP を見つけたら、新しく買うのをやめて降りる。

import { existsSync, appendFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { recentCandles, ticker } from './exchange.mjs';
import { TIMEFRAMES } from './candles.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const 停止ファイル = join(HERE, '..', 'STOP');
const 記録先 = join(HERE, '..', 'state');

const 待つ = (ms) => new Promise((r) => setTimeout(r, ms));
const 時刻 = () => new Date().toISOString().replace('T', ' ').slice(0, 19);

export async function runLive(o) {
  const {
    exchange, pair, tf, strategy,
    sizeFrac = 1.0, maxOrderJpy = 10_000, minAmount = 0.0001,
    dailyLossLimit = 0.05, maxDrawdownStop = 0.2,
    once = false,
  } = o;

  const spec = TIMEFRAMES[tf];
  const 記録 = (s) => {
    const 行 = `[${時刻()}] ${s}`;
    console.log(行);
    try {
      if (!existsSync(記録先)) mkdirSync(記録先, { recursive: true });
      appendFileSync(join(記録先, `${pair}_${tf}.log`), 行 + '\n', 'utf8');
    } catch { /* 記録に失敗しても売買は続ける */ }
  };

  記録(`開始 ${exchange.名前}｜${pair} ${tf}｜${strategy.name} ${JSON.stringify(strategy.params)}`);
  記録(`1回の上限 ${maxOrderJpy.toLocaleString('ja-JP')}円｜日次の損切り ${(dailyLossLimit * 100).toFixed(0)}%｜通算の下落上限 ${(maxDrawdownStop * 100).toFixed(0)}%`);
  if (exchange.実弾) 記録('⚠ 実弾モード。本物のお金が動く。');

  let 山 = null;
  let 日付 = null;
  let 日の初め = null;
  let 止まった = false;
  let 連続しくじり = 0;
  const しくじり上限 = 5;

  while (true) {
    try {
      if (existsSync(停止ファイル)) {
        記録('STOP ファイルを見つけた。新規は取らない。');
        止まった = true;
      }

      const 足 = await recentCandles(pair, tf, strategy.warmup + 5);
      if (足.length < strategy.warmup + 2) {
        連続しくじり++;
        記録(`足が足りない（${足.length}本／必要 ${strategy.warmup + 2}本）。${連続しくじり}回目。`);
        if (once || 連続しくじり >= しくじり上限) {
          記録(
            `足がそろわないので終わる。${tf} は ${strategy.name} に必要な本数（${strategy.warmup + 2}本）を` +
            'その取引所から取れていない。もっと短い足にするか、戦略の設定を小さくすること。',
          );
          return;
        }
        await 待つ(60_000);
        continue;
      }
      連続しくじり = 0;

      const 現在値 = (await ticker(pair)).最終価格;
      const 残高 = await exchange.balance();
      const 持ち数量 = 残高.base ?? 残高.全部?.[pair.split('_')[0]] ?? 0;
      const 資産 = 残高.jpy + 持ち数量 * 現在値;

      // 日をまたいだら、その日の出発点を取り直す
      const 今日 = new Date().toISOString().slice(0, 10);
      if (今日 !== 日付) { 日付 = 今日; 日の初め = 資産; 記録(`— ${今日} 開始 資産 ${Math.round(資産).toLocaleString('ja-JP')}円`); }
      山 = 山 === null ? 資産 : Math.max(山, 資産);

      // 安全装置
      let 新規禁止 = 止まった;
      if (資産 <= 日の初め * (1 - dailyLossLimit)) {
        記録(`⚠ 今日の下げが上限に達した（${Math.round(資産).toLocaleString('ja-JP')}円）。今日はもう買わない。`);
        新規禁止 = true;
      }
      if (資産 <= 山 * (1 - maxDrawdownStop)) {
        記録(`⚠ 山から${(maxDrawdownStop * 100).toFixed(0)}%減った。売買を打ち切る。`);
        新規禁止 = true;
        止まった = true;
      }

      const 合図 = strategy.signals(足);
      const 欲しい持ち高 = 新規禁止 ? 0 : 合図[足.length - 1];
      const 今の持ち高 = 持ち数量 >= minAmount ? 1 : 0;

      記録(
        `${new Date(足.at(-1).t).toISOString().slice(0, 16)} 終値 ${足.at(-1).c.toLocaleString('ja-JP')}｜` +
        `今 ${今の持ち高 ? '持っている' : '現金'}／したい ${欲しい持ち高 ? '持つ' : '現金'}｜資産 ${Math.round(資産).toLocaleString('ja-JP')}円`,
      );

      if (欲しい持ち高 !== 今の持ち高) {
        if (欲しい持ち高 === 1) {
          const 使う額 = Math.min(残高.jpy * sizeFrac, maxOrderJpy);
          const 数量 = 切り捨て(使う額 / 現在値, 8);
          if (数量 < minAmount) {
            記録(`買えない。必要な最小数量 ${minAmount} に対し ${数量}（残高 ${Math.round(残高.jpy).toLocaleString('ja-JP')}円）`);
          } else {
            const r = await exchange.buy(pair, 数量);
            記録(`▲ 買った ${r.数量} @ ${Math.round(r.値段).toLocaleString('ja-JP')}円`);
          }
        } else {
          const 数量 = 切り捨て(持ち数量, 8);
          if (数量 >= minAmount) {
            const r = await exchange.sell(pair, 数量);
            記録(`▼ 売った ${r.数量} @ ${Math.round(r.値段).toLocaleString('ja-JP')}円`);
          }
        }
      }

      if (once) { 記録('1回だけの指定なので終わる。'); return; }
      if (止まった && 今の持ち高 === 0) { 記録('打ち切り済みで持ち高も無い。終わる。'); return; }
    } catch (e) {
      連続しくじり++;
      記録(`エラー（${連続しくじり}回目）: ${e.message}`);
      if (once) return;
      if (連続しくじり >= しくじり上限) {
        記録(`${しくじり上限}回続けて失敗した。黙って回り続けても仕方ないので終わる。`);
        return;
      }
    }

    const 次 = 次の足まで(spec.ms);
    await 待つ(次 + 5_000); // 足が確定してから少し置いて取りに行く
  }
}

function 次の足まで(足の長さms) {
  const 今 = Date.now();
  return 足の長さms - (今 % 足の長さms);
}

function 切り捨て(n, 桁) {
  const k = 10 ** 桁;
  return Math.floor(n * k) / k;
}
