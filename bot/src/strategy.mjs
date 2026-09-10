// 売買のルール（戦略）。
//
// どの戦略も「その足の終値まで見て、次にどうしたいか」を返すだけ。
//   1 = 買って持っていたい / 0 = 持ちたくない（現金でいたい）
//
// 大事な決まりごと:
//   i 番目の足の判断に、i+1 番目より先の情報を絶対に使わない。
//   これを破ると、バックテストの成績は本物そっくりの嘘になる。
//   selftest がこの点を毎回検査している。

// 現物（買って売るだけ）を前提にしている。売りから入る建て方はしない。
// 追証もロスカットもなく、最悪でも買った額しか減らないため。

export const STRATEGIES = {
  'sma-cross': {
    name: '移動平均クロス',
    説明: '短い平均が長い平均を上回っている間だけ持つ。上げ相場に乗る型。',
    defaults: { fast: 20, slow: 60 },
    warmup: (p) => p.slow + 1,
    signals(candles, p) {
      const close = candles.map((k) => k.c);
      const fast = sma(close, p.fast);
      const slow = sma(close, p.slow);
      return close.map((_, i) =>
        fast[i] !== null && slow[i] !== null && fast[i] > slow[i] ? 1 : 0,
      );
    },
  },

  donchian: {
    name: 'ドンチャン抜け',
    説明: '直近N本の高値を終値で抜けたら持つ。安値を割ったら降りる。',
    defaults: { entry: 20, exit: 10 },
    warmup: (p) => Math.max(p.entry, p.exit) + 1,
    signals(candles, p) {
      const out = new Array(candles.length).fill(0);
      let pos = 0;
      for (let i = 0; i < candles.length; i++) {
        const need = Math.max(p.entry, p.exit);
        if (i < need) { out[i] = 0; continue; }
        // 「直前のN本」だけを見る。今の足の高安は含めない。
        let hi = -Infinity, lo = Infinity;
        for (let j = i - p.entry; j < i; j++) hi = Math.max(hi, candles[j].h);
        for (let j = i - p.exit; j < i; j++) lo = Math.min(lo, candles[j].l);
        const c = candles[i].c;
        if (pos === 0 && c > hi) pos = 1;
        else if (pos === 1 && c < lo) pos = 0;
        out[i] = pos;
      }
      return out;
    },
  },

  rsi: {
    name: 'RSI逆張り',
    説明: '下がりすぎたら買い、上がりすぎたら売る。横ばい相場向き。',
    defaults: { period: 14, buy: 30, sell: 70 },
    warmup: (p) => p.period + 2,
    signals(candles, p) {
      const r = rsi(candles.map((k) => k.c), p.period);
      const out = new Array(candles.length).fill(0);
      let pos = 0;
      for (let i = 0; i < candles.length; i++) {
        if (r[i] === null) { out[i] = 0; continue; }
        if (pos === 0 && r[i] < p.buy) pos = 1;
        else if (pos === 1 && r[i] > p.sell) pos = 0;
        out[i] = pos;
      }
      return out;
    },
  },

  'buy-hold': {
    name: '買って持ちっぱなし',
    説明: '最初に買って何もしない。他の戦略はこれに勝てて初めて意味がある。',
    defaults: {},
    warmup: () => 1,
    signals(candles) {
      return candles.map((_, i) => (i === 0 ? 0 : 1));
    },
  },
};

export function makeStrategy(key, overrides = {}) {
  const def = STRATEGIES[key];
  if (!def) {
    throw new Error(`知らない戦略: ${key}（使えるのは ${Object.keys(STRATEGIES).join(', ')}）`);
  }
  const params = { ...def.defaults, ...overrides };
  return {
    key,
    name: def.name,
    説明: def.説明,
    params,
    warmup: def.warmup(params),
    signals: (candles) => def.signals(candles, params),
  };
}

// --- 計算の部品 -------------------------------------------------------

// 単純移動平均。i 番目には i を含む直近 n 本の平均が入る。足りない間は null。
export function sma(values, n) {
  const out = new Array(values.length).fill(null);
  if (n <= 0) return out;
  let sum = 0;
  for (let i = 0; i < values.length; i++) {
    sum += values[i];
    if (i >= n) sum -= values[i - n];
    if (i >= n - 1) out[i] = sum / n;
  }
  return out;
}

// RSI（ワイルダーの平滑化）。
export function rsi(values, n) {
  const out = new Array(values.length).fill(null);
  if (values.length <= n) return out;
  let gain = 0, loss = 0;
  for (let i = 1; i <= n; i++) {
    const d = values[i] - values[i - 1];
    if (d >= 0) gain += d; else loss -= d;
  }
  gain /= n; loss /= n;
  out[n] = loss === 0 ? 100 : 100 - 100 / (1 + gain / loss);
  for (let i = n + 1; i < values.length; i++) {
    const d = values[i] - values[i - 1];
    gain = (gain * (n - 1) + (d > 0 ? d : 0)) / n;
    loss = (loss * (n - 1) + (d < 0 ? -d : 0)) / n;
    out[i] = loss === 0 ? 100 : 100 - 100 / (1 + gain / loss);
  }
  return out;
}
