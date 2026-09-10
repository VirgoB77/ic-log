#!/usr/bin/env node
// 売買botの入口。
//
//   node bot.mjs selftest                    エンジンの検算（まずこれ）
//   node bot.mjs fetch    --pair btc_jpy --tf 1day --from 2021-01-01
//   node bot.mjs backtest --pair btc_jpy --tf 1day --strategy sma-cross
//   node bot.mjs compare  --pair btc_jpy --tf 1day
//   node bot.mjs check                       鍵が正しいか確かめる（残高を読むだけ）
//   node bot.mjs paper    --pair btc_jpy --tf 1hour --strategy donchian
//   node bot.mjs live     --pair btc_jpy --tf 1hour --strategy donchian --live
//
// 順番が大事。selftest → backtest → paper を通してからでないと live は意味がない。

import { readFileSync, existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createInterface } from 'node:readline/promises';
import { backtest, DEFAULTS } from './src/engine.mjs';
import { formatReport, formatTable } from './src/report.mjs';
import { makeStrategy, STRATEGIES } from './src/strategy.mjs';
import { fetchCandles, saveCache, loadCache, loadCsv, TIMEFRAMES } from './src/candles.mjs';
import { PaperExchange, BitbankExchange } from './src/exchange.mjs';
import { runLive } from './src/live.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
読み込むenv(join(HERE, '.env'));

const [, , 命令, ...残り] = process.argv;
const 引数 = 解く(残り);

try {
  await 実行(命令, 引数);
} catch (e) {
  console.error(`\n✗ ${e.message}\n`);
  process.exit(1);
}

async function 実行(命令, a) {
  switch (命令) {
    case 'selftest': return await import('./selftest.mjs');
    case 'fetch': return await 取得(a);
    case 'backtest': return await 検証(a);
    case 'compare': return await 比べる(a);
    case 'check': return await 鍵の確認();
    case 'paper': return await 回す(a, false);
    case 'live': return await 回す(a, true);
    default: return 使い方();
  }
}

// --- 過去データを取ってくる -------------------------------------------

async function 取得(a) {
  const pair = a.pair ?? 'btc_jpy';
  const tf = a.tf ?? '1day';
  const from = new Date(a.from ?? '2021-01-01');
  const to = new Date(a.to ?? new Date().toISOString().slice(0, 10));
  console.log(`${pair} の ${tf} 足を ${日(from)} から ${日(to)} まで取ってくる…`);
  const 足 = await fetchCandles(pair, tf, from, to);
  saveCache(pair, tf, 足);
  console.log(`${足.length}本 取った。${日(足[0].t)} 〜 ${日(足.at(-1).t)}`);
}

function 足を用意(a) {
  if (a.csv) {
    const 足 = loadCsv(resolve(a.csv));
    console.log(`${a.csv} から ${足.length}本 読んだ`);
    return 足;
  }
  const pair = a.pair ?? 'btc_jpy';
  const tf = a.tf ?? '1day';
  const 足 = loadCache(pair, tf);
  if (!足?.length) {
    throw new Error(
      `${pair} ${tf} のデータが無い。先に取ってくること:\n` +
      `    node bot.mjs fetch --pair ${pair} --tf ${tf} --from 2021-01-01`,
    );
  }
  const from = a.from ? Date.parse(a.from) : -Infinity;
  const to = a.to ? Date.parse(a.to) : Infinity;
  const 絞った = 足.filter((k) => k.t >= from && k.t <= to);
  if (!絞った.length) throw new Error('指定した期間に足が1本も無い');
  return 絞った;
}

function 設定(a) {
  return {
    cash: 数(a.cash, DEFAULTS.cash),
    feeRate: 数(a.fee, DEFAULTS.feeRate),
    slippageBps: 数(a.slippage, DEFAULTS.slippageBps),
    sizeFrac: 数(a.size, DEFAULTS.sizeFrac),
    maxDrawdownStop: a['max-dd'] ? 数(a['max-dd']) : null,
    dailyLossLimit: a['daily-loss'] ? 数(a['daily-loss']) : null,
  };
}

async function 検証(a) {
  const 足 = 足を用意(a);
  const key = a.strategy ?? 'sma-cross';
  const s = makeStrategy(key, 数値だけ(a));
  const 共通 = 設定(a);
  const r = backtest({ candles: 足, strategy: s, ...共通 });
  const 基準 = backtest({ candles: 足, strategy: makeStrategy('buy-hold'), ...共通 });
  console.log(formatReport(r, key === 'buy-hold' ? null : 基準));
}

async function 比べる(a) {
  const 足 = 足を用意(a);
  const 共通 = 設定(a);
  const 結果 = Object.keys(STRATEGIES).map((k) =>
    backtest({ candles: 足, strategy: makeStrategy(k, 数値だけ(a)), ...共通 }),
  );
  console.log(`\n${日(足[0].t)} 〜 ${日(足.at(-1).t)}（${足.length}本）｜元手 ${共通.cash.toLocaleString('ja-JP')}円｜手数料 ${(共通.feeRate * 100).toFixed(3)}%`);
  console.log(formatTable(結果));
  const 持ちっぱなし = 結果.find((r) => r.戦略 === STRATEGIES['buy-hold'].name);
  const 勝った = 結果.filter((r) => r !== 持ちっぱなし && r.最終資産 > 持ちっぱなし.最終資産);
  console.log(
    勝った.length
      ? `  持ちっぱなしに勝ったのは ${勝った.map((r) => r.戦略).join('、')}。\n` +
        '  ただしこれは過去にたまたま合っただけかもしれない。期間を変えて何度も試すこと。\n'
      : '  どれも「買って持ちっぱなし」に勝てていない。この足・この期間では、売買する価値がない。\n',
  );
}

// --- 実際に回す -------------------------------------------------------

async function 鍵の確認() {
  const ex = new BitbankExchange({
    key: process.env.BITBANK_API_KEY,
    secret: process.env.BITBANK_API_SECRET,
  });
  console.log('残高を読むだけの呼び出しで、鍵と署名が通るか確かめる…');
  const b = await ex.balance();
  console.log('\n✓ 鍵は通った。残高:');
  for (const [名, 量] of Object.entries(b.全部)) if (Number(量) > 0) console.log(`   ${名}: ${量}`);
  console.log('\nここが通れば発注もできる見込み。ただし最初は必ず小さい額で試すこと。\n');
}

async function 回す(a, 実弾) {
  const pair = a.pair ?? 'btc_jpy';
  const tf = a.tf ?? '1hour';
  if (!TIMEFRAMES[tf]) throw new Error(`知らない足の種類: ${tf}`);
  const s = makeStrategy(a.strategy ?? 'donchian', 数値だけ(a));

  let ex;
  if (実弾) {
    await 実弾の関門(a);
    ex = new BitbankExchange({
      key: process.env.BITBANK_API_KEY,
      secret: process.env.BITBANK_API_SECRET,
    });
  } else {
    ex = new PaperExchange({
      pair,
      cash: 数(a.cash, DEFAULTS.cash),
      feeRate: 数(a.fee, DEFAULTS.feeRate),
      slippageBps: 数(a.slippage, DEFAULTS.slippageBps),
    });
  }

  await runLive({
    exchange: ex, pair, tf, strategy: s,
    sizeFrac: 数(a.size, 1.0),
    maxOrderJpy: 数(a['max-order'], 10_000),
    minAmount: 数(a['min-amount'], 0.0001),
    dailyLossLimit: 数(a['daily-loss'], 0.05),
    maxDrawdownStop: 数(a['max-dd'], 0.2),
    once: !!a.once,
  });
}

// 実弾を出す前の関門。3つ揃わないと通さない。
async function 実弾の関門(a) {
  if (!a.live) {
    throw new Error('実弾で回すには --live を付けること。付いていないので何もしない。');
  }
  if (process.env.BOT_LIVE_OK !== 'yes') {
    throw new Error(
      '.env の BOT_LIVE_OK が yes になっていない。\n' +
      '  うっかり実弾で起動しないための仕掛け。本当に回すときだけ自分で書き換えること。',
    );
  }
  if (!process.stdin.isTTY) {
    throw new Error(
      '実弾の初回は、人が見ている画面からしか始められない。\n' +
      '  自動起動（systemd や cron）に載せるのは、紙で十分に回してからにすること。',
    );
  }
  const 上限 = 数(a['max-order'], 10_000);
  console.log(`
${'━'.repeat(56)}
  ⚠ これから本物のお金で売買する
${'━'.repeat(56)}

  取引所   bitbank
  通貨ペア ${a.pair ?? 'btc_jpy'}
  1回の上限 ${上限.toLocaleString('ja-JP')}円

  確かめること:
   ・node bot.mjs selftest は通ったか
   ・この戦略でバックテストして、買って持ちっぱなしに勝ったか
   ・紙トレードを何日か回して、思ったとおりに動いたか
   ・この金額は、全部無くなっても暮らしが変わらない額か

  自動売買は「勝ち方」ではなく「同じ判断を繰り返す道具」でしかない。
  負ける戦略を載せれば、より速く正確に負ける。
`);
  const rl = createInterface({ input: process.stdin, output: process.stdout });
  const 答え = await rl.question('  本当に始めるなら「実弾で回す」と打つ > ');
  rl.close();
  if (答え.trim() !== '実弾で回す') throw new Error('打ち込みが違ったので始めない。');
}

// --- 細かい道具 -------------------------------------------------------

function 使い方() {
  console.log(`
高速IC乗降記録リポジトリの売買bot

  node bot.mjs selftest
      エンジンの検算。最初にこれを通す。

  node bot.mjs fetch --pair btc_jpy --tf 1day --from 2021-01-01
      過去のローソク足を取ってきて data/ に貯める。

  node bot.mjs backtest --pair btc_jpy --tf 1day --strategy sma-cross --fast 20 --slow 60
      過去データで成績を出す。手数料とすべりを引いた後の数字。

  node bot.mjs compare --pair btc_jpy --tf 1day
      戦略を全部並べて、買って持ちっぱなしと比べる。

  node bot.mjs check
      APIキーが正しいか確かめる。残高を読むだけで発注はしない。

  node bot.mjs paper --pair btc_jpy --tf 1hour --strategy donchian
      値段は本物、注文は嘘。お金は動かない。

  node bot.mjs live --pair btc_jpy --tf 1hour --strategy donchian --live --max-order 5000
      実弾。--live と .env の BOT_LIVE_OK=yes と手打ちの確認が要る。

戦略:
${Object.entries(STRATEGIES).map(([k, v]) => `  ${k.padEnd(12)} ${v.name} … ${v.説明}`).join('\n')}

主な指定:
  --cash 300000      元手（円）
  --fee 0.0012       手数料の率。取引所の最新の料率を自分で確かめて入れる
  --slippage 5       すべり（bps）
  --size 1.0         1回に元手の何割を使うか
  --max-order 10000  1回の注文の上限（円）
  --daily-loss 0.05  その日これだけ減ったら打ち止め
  --max-dd 0.2       山からこれだけ減ったら売買をやめる
  --csv path.csv     取引所ではなくCSVを読む（株や為替のデータ用）
`);
}

function 解く(argv) {
  const a = {};
  for (let i = 0; i < argv.length; i++) {
    if (!argv[i].startsWith('--')) continue;
    const 名 = argv[i].slice(2);
    const 次 = argv[i + 1];
    if (次 === undefined || 次.startsWith('--')) a[名] = true;
    else { a[名] = 次; i++; }
  }
  return a;
}

// 戦略の細かい数字（--fast 20 など）だけ抜き出す
function 数値だけ(a) {
  const 除く = new Set([
    'pair', 'tf', 'strategy', 'cash', 'fee', 'slippage', 'size',
    'max-order', 'min-amount', 'daily-loss', 'max-dd', 'csv', 'from', 'to', 'live', 'once',
  ]);
  const out = {};
  for (const [k, v] of Object.entries(a)) {
    if (除く.has(k)) continue;
    const n = Number(v);
    if (Number.isFinite(n)) out[k] = n;
  }
  return out;
}

function 数(v, 既定) {
  if (v === undefined || v === true) return 既定;
  const n = Number(v);
  if (!Number.isFinite(n)) throw new Error(`数字で指定すること: ${v}`);
  return n;
}

function 日(t) { return new Date(t).toISOString().slice(0, 10); }

function 読み込むenv(path) {
  if (!existsSync(path)) return;
  for (const 行 of readFileSync(path, 'utf8').split(/\r?\n/)) {
    const m = 行.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/);
    if (m && !process.env[m[1]]) process.env[m[1]] = m[2].trim().replace(/^["']|["']$/g, '');
  }
}
