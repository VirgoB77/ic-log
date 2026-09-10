// エンジンの検算。`node selftest.mjs` で走る。
//
// バックテストは、間違っていても「それらしい数字」を出してしまう。
// だから、間違っていたら必ず落ちる形の検査を並べてある。

import { backtest } from './src/engine.mjs';
import { metrics } from './src/report.mjs';
import { STRATEGIES, makeStrategy, sma, rsi } from './src/strategy.mjs';
import { synthCandles, dedupe, loadCsv } from './src/candles.mjs';

let 通過 = 0;
let 失敗 = 0;

function 検査(名, fn) {
  try {
    fn();
    通過++;
    console.log(`  ✓ ${名}`);
  } catch (e) {
    失敗++;
    console.log(`  ✗ ${名}\n      ${e.message}`);
  }
}

function 等しい(a, b, 名, 許容 = 1e-9) {
  if (Math.abs(a - b) > 許容) throw new Error(`${名}: ${a} ≠ ${b}`);
}
function 真(cond, 名) {
  if (!cond) throw new Error(名);
}

// ── 1. 未来を覗いていないか ────────────────────────────────
// i 本目までしか渡さずに計算した答えが、全部渡したときと変わってはいけない。
// 変わるなら、その戦略は「まだ起きていないこと」を見て判断している。

function 覗き見を探す(strategy, candles) {
  const 全体 = strategy.signals(candles);
  const 見る場所 = [];
  for (let i = strategy.warmup + 1; i < candles.length; i += 17) 見る場所.push(i);
  for (const i of 見る場所) {
    const 途中まで = strategy.signals(candles.slice(0, i + 1));
    if (途中まで[i] !== 全体[i]) {
      return `${i}本目の判断が変わる（途中まで=${途中まで[i]} 全部=${全体[i]}）`;
    }
  }
  return null;
}

const 相場 = synthCandles({ bars: 800, seed: 7 });

console.log('\n【1】未来を覗いていないか');
for (const key of Object.keys(STRATEGIES)) {
  検査(`${key} は過去だけを見て判断している`, () => {
    const 見つかった = 覗き見を探す(makeStrategy(key), 相場);
    真(見つかった === null, `覗き見あり: ${見つかった}`);
  });
}

// 検査そのものが働いているか。わざと未来を覗く戦略を出して、捕まえられるか試す。
検査('【重要】覗き見の検査自体が働いている（ズルする戦略を捕まえられる）', () => {
  const ズル = {
    name: 'ズル', warmup: 1,
    signals: (c) => c.map((_, i) => (i + 1 < c.length && c[i + 1].c > c[i].c ? 1 : 0)),
  };
  真(覗き見を探す(ズル, 相場) !== null, 'ズルを見逃した。この検査は意味をなしていない');
});

// ── 2. 約定の値段は正しいか ────────────────────────────────
console.log('\n【2】約定は「次の足の始値」で通っているか');

検査('終値を見た瞬間にその終値で買ってしまっていない', () => {
  const c = [
    { t: d(0), o: 100, h: 100, l: 100, c: 100, v: 1 },
    { t: d(1), o: 100, h: 100, l: 100, c: 100, v: 1 },
    { t: d(2), o: 100, h: 200, l: 100, c: 200, v: 1 }, // ここで買いの合図
    { t: d(3), o: 150, h: 150, l: 150, c: 150, v: 1 }, // 実際に買えるのは翌足の150
    { t: d(4), o: 150, h: 150, l: 150, c: 150, v: 1 },
  ];
  const s = { name: '手動', warmup: 0, signals: () => [0, 0, 1, 1, 1] };
  const r = backtest({ candles: c, strategy: s, cash: 1000, feeRate: 0, slippageBps: 0 });
  // 150で買って150で終わるので、資産は元手のまま。
  // もし200（合図の足の終値）で買っていたら 750 に減る。
  等しい(r.最終資産, 1000, '最終資産', 1e-6);
});

検査('すべりは自分に不利な側へ倒れている', () => {
  const c = 平らな相場(10, 100);
  const s = { name: '手動', warmup: 0, signals: (k) => k.map((_, i) => (i >= 1 ? 1 : 0)) };
  const なし = backtest({ candles: c, strategy: s, cash: 1000, feeRate: 0, slippageBps: 0 });
  const あり = backtest({ candles: c, strategy: s, cash: 1000, feeRate: 0, slippageBps: 50 });
  等しい(なし.最終資産, 1000, 'すべりなしなら増減なし', 1e-6);
  真(あり.最終資産 < なし.最終資産, 'すべりを入れたのに資産が減っていない');
});

// ── 3. 費用がきちんと引かれているか ──────────────────────────
console.log('\n【3】手数料は引かれているか');

検査('手数料を上げると成績は必ず悪くなる', () => {
  const s = makeStrategy('sma-cross');
  const 安い = backtest({ candles: 相場, strategy: s, feeRate: 0.0001 });
  const 高い = backtest({ candles: 相場, strategy: s, feeRate: 0.005 });
  真(高い.最終資産 < 安い.最終資産, '手数料を上げたのに成績が悪くなっていない');
  真(高い.手数料合計 > 安い.手数料合計, '手数料合計が増えていない');
});

検査('取引ごとの損益の合計が、資産の増減とぴったり合う', () => {
  const r = backtest({ candles: 相場, strategy: makeStrategy('donchian') });
  const 合計 = r.trades.reduce((s, t) => s + t.損益, 0);
  等しい(合計, r.最終資産 - r.開始資産, '損益の合計と資産の増減', 1e-6);
});

検査('手数料は損益のうちに勘定されている（手数料ゼロなら成績は必ず良くなる）', () => {
  const s = makeStrategy('sma-cross');
  const 現実 = backtest({ candles: 相場, strategy: s, feeRate: 0.0012, slippageBps: 5 });
  const 夢 = backtest({ candles: 相場, strategy: s, feeRate: 0, slippageBps: 0 });
  真(夢.最終資産 > 現実.最終資産, '費用を消したのに成績が変わらない');
});

// ── 4. ありえない状態にならないか ────────────────────────────
console.log('\n【4】ありえない状態になっていないか');

検査('資産が負にならない・売買しなければ元手のまま', () => {
  const 何もしない = { name: '何もしない', warmup: 0, signals: (c) => c.map(() => 0) };
  const r = backtest({ candles: 相場, strategy: 何もしない, cash: 300_000 });
  等しい(r.最終資産, 300_000, '売買しなければ元手のまま', 1e-6);
  等しい(r.trades.length, 0, '取引回数');
  真(r.equity.every((e) => e.equity > 0), '資産が0以下になっている足がある');
});

検査('資産の記録の本数が足の本数と一致する', () => {
  const r = backtest({ candles: 相場, strategy: makeStrategy('rsi') });
  等しい(r.equity.length, 相場.length, '記録の本数');
});

検査('最後は必ず手仕舞いされ、持ち越しが残らない', () => {
  const r = backtest({ candles: 相場, strategy: makeStrategy('buy-hold') });
  真(r.equity[r.equity.length - 1].pos === 0, '最後まで持ったままになっている');
  真(r.trades.length > 0, '買って持ちっぱなしなのに取引が1件もない');
});

検査('データが短すぎるときは黙って動かず、はっきり止まる', () => {
  let 止まった = false;
  try {
    backtest({ candles: 相場.slice(0, 10), strategy: makeStrategy('sma-cross') });
  } catch (e) {
    止まった = /足が足りない/.test(e.message);
  }
  真(止まった, '足が足りないのに動いてしまった');
});

// ── 5. 安全装置は効くか ────────────────────────────────────
console.log('\n【5】安全装置は効くか');

検査('下落が上限を超えたら売買を止める', () => {
  const 暴落 = 下がり続ける相場(200, 1000);
  const 全部買う = { name: '全部買う', warmup: 0, signals: (c) => c.map((_, i) => (i >= 1 ? 1 : 0)) };
  const 上限なし = backtest({ candles: 暴落, strategy: 全部買う, cash: 100_000, feeRate: 0, slippageBps: 0 });
  const 上限あり = backtest({
    candles: 暴落, strategy: 全部買う, cash: 100_000, feeRate: 0, slippageBps: 0,
    maxDrawdownStop: 0.2,
  });
  真(上限あり.停止した, '暴落しているのに停止していない');
  真(上限あり.最終資産 > 上限なし.最終資産, '安全装置を入れたのに損が減っていない');
  真(上限あり.最終資産 > 100_000 * 0.7, `止まりが遅すぎる（${Math.round(上限あり.最終資産)}円まで減った）`);
});

// ── 6. 計算の部品 ──────────────────────────────────────────
console.log('\n【6】計算の部品は合っているか');

検査('移動平均の値が手計算と合う', () => {
  const v = [1, 2, 3, 4, 5, 6];
  const s = sma(v, 3);
  真(s[0] === null && s[1] === null, '本数が足りない間は空でなければならない');
  等しい(s[2], 2, '(1+2+3)/3');
  等しい(s[5], 5, '(4+5+6)/3');
});

検査('上げ続ければRSIは100、下げ続ければ0に寄る', () => {
  const 上げ = Array.from({ length: 40 }, (_, i) => 100 + i);
  const 下げ = Array.from({ length: 40 }, (_, i) => 100 - i);
  真(rsi(上げ, 14).at(-1) > 99, `上げ続けたRSIが ${rsi(上げ, 14).at(-1)}`);
  真(rsi(下げ, 14).at(-1) < 1, `下げ続けたRSIが ${rsi(下げ, 14).at(-1)}`);
});

検査('同じ時刻の足が重複しても1本にまとまり、古い順に並ぶ', () => {
  const 雑 = [
    { t: 300, o: 3, h: 3, l: 3, c: 3, v: 1 },
    { t: 100, o: 1, h: 1, l: 1, c: 1, v: 1 },
    { t: 300, o: 9, h: 9, l: 9, c: 9, v: 1 },
    { t: 200, o: 2, h: 2, l: 2, c: 2, v: 1 },
  ];
  const r = dedupe(雑);
  等しい(r.length, 3, '本数');
  真(r[0].t < r[1].t && r[1].t < r[2].t, '時刻順に並んでいない');
});

// ── 7. 集計は正しいか ──────────────────────────────────────
console.log('\n【7】成績の集計は正しいか');

検査('勝率・平均損益が取引の中身と一致する', () => {
  const r = backtest({ candles: 相場, strategy: makeStrategy('donchian') });
  const m = metrics(r);
  const 勝ち = r.trades.filter((t) => t.損益 > 0);
  等しい(m.勝率, 勝ち.length / r.trades.length, '勝率', 1e-12);
  等しい(m.取引回数, r.trades.length, '取引回数');
  真(m.最大ドローダウン >= 0 && m.最大ドローダウン <= 1, `最大下落が範囲外: ${m.最大ドローダウン}`);
});

検査('右肩上がりの相場では最大下落がほぼ0になる', () => {
  const 上げ相場 = 上がり続ける相場(300, 1000);
  const r = backtest({
    candles: 上げ相場, strategy: makeStrategy('buy-hold'), feeRate: 0, slippageBps: 0,
  });
  const m = metrics(r);
  真(m.最大ドローダウン < 0.01, `上げ相場なのに ${m.最大ドローダウン} 下落している`);
  真(m.純損益 > 0, '上げ相場を持ちっぱなしで負けている');
});

// ── 部品 ──────────────────────────────────────────────────
function d(i) { return Date.UTC(2020, 0, 1) + i * 86_400_000; }
function 平らな相場(n, p) {
  return Array.from({ length: n }, (_, i) => ({ t: d(i), o: p, h: p, l: p, c: p, v: 1 }));
}
function 下がり続ける相場(n, p) {
  return Array.from({ length: n }, (_, i) => {
    const v = p * 0.98 ** i;
    return { t: d(i), o: v, h: v, l: v, c: v, v: 1 };
  });
}
function 上がり続ける相場(n, p) {
  return Array.from({ length: n }, (_, i) => {
    const v = p * 1.01 ** i;
    return { t: d(i), o: v, h: v, l: v, c: v, v: 1 };
  });
}

console.log(`\n${'━'.repeat(50)}`);
console.log(`  通過 ${通過} / 失敗 ${失敗}`);
console.log(`${'━'.repeat(50)}\n`);
process.exit(失敗 === 0 ? 0 : 1);
