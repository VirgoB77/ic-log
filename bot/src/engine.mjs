// 売買の実行エンジン。過去データを1本ずつ流して、実際に売買したらどうなったかを出す。
//
// 約定のきまり:
//   足 i の「終値」を見て判断し、注文は足 i+1 の「始値」で通る。
//   終値を見た瞬間にその終値で買えることにすると、現実には取れない利益が乗る。
//
// 費用は必ず引く:
//   手数料 … 売買のたびに約定代金にかける
//   すべり … 買いは高く、売りは安く約定させる（自分に不利な側へ倒す）

export const DEFAULTS = {
  cash: 300_000,       // 元手（円）
  feeRate: 0.0012,     // 手数料 0.12%。取引所の最新の料率を必ず自分で確かめること
  slippageBps: 5,      // すべり 0.05%
  sizeFrac: 1.0,       // 1回に元手の何割を使うか
  maxDrawdownStop: null, // 例 0.3 … 資産が山から3割減ったら以後いっさい売買しない
  dailyLossLimit: null,  // 例 0.05 … その日の頭から5%減ったらその日は打ち止め
};

export function backtest(options) {
  const o = { ...DEFAULTS, ...options };
  const { candles, strategy } = o;
  if (!candles?.length) throw new Error('ローソク足が空。データを取ってくること');
  if (candles.length < strategy.warmup + 3) {
    throw new Error(
      `足が足りない。${strategy.name} には最低 ${strategy.warmup + 3} 本要るが ${candles.length} 本しかない`,
    );
  }

  const signals = strategy.signals(candles);
  const slip = o.slippageBps / 10_000;

  let cash = o.cash;
  let units = 0;          // 持っている数量
  let pos = 0;            // 0=現金 1=持っている
  let entry = null;       // 建てたときの記録
  let pending = null;     // 次の足の頭で持ちたい状態
  let feesPaid = 0;
  let peak = o.cash;
  let halted = false;     // ドローダウン上限に当たって完全停止した
  let dayKey = null;
  let dayStartEquity = o.cash;
  let dayBlocked = false;

  const trades = [];
  const equity = [];

  for (let i = 0; i < candles.length; i++) {
    const k = candles[i];

    // (1) 前の足の終わりに決めた注文を、この足の始値で約定させる
    if (i > 0 && pending !== null && pending !== pos) {
      if (pending === 1) {
        const price = k.o * (1 + slip);
        const spend = cash * o.sizeFrac;
        const fee = spend * o.feeRate;
        const got = (spend - fee) / price;
        if (got > 0 && spend > 0) {
          cash -= spend;
          units += got;
          feesPaid += fee;
          pos = 1;
          entry = { t: k.t, price, units: got, fee };
        }
      } else {
        const price = k.o * (1 - slip);
        const gross = units * price;
        const fee = gross * o.feeRate;
        cash += gross - fee;
        feesPaid += fee;
        if (entry) {
          const cost = entry.units * entry.price + entry.fee;
          trades.push({
            入り時刻: entry.t,
            出た時刻: k.t,
            入り値: entry.price,
            出た値: price,
            数量: entry.units,
            手数料: entry.fee + fee,
            損益: gross - fee - cost,
            損益率: (gross - fee - cost) / cost,
          });
        }
        units = 0;
        pos = 0;
        entry = null;
      }
    }

    // (2) この足の終値で資産を評価する
    const eq = cash + units * k.c;
    equity.push({ t: k.t, equity: eq, pos });
    peak = Math.max(peak, eq);

    // (3) 日をまたいだら、その日の出発点を取り直す
    const kd = new Date(k.t).toISOString().slice(0, 10);
    if (kd !== dayKey) {
      dayKey = kd;
      dayStartEquity = eq;
      dayBlocked = false;
    }

    // (4) 安全装置を確かめる
    if (o.maxDrawdownStop !== null && eq <= peak * (1 - o.maxDrawdownStop)) halted = true;
    if (o.dailyLossLimit !== null && eq <= dayStartEquity * (1 - o.dailyLossLimit)) dayBlocked = true;

    // (5) この足の終値を見て、次の足の頭でどうするかを決める
    if (halted) {
      pending = 0;                       // 完全停止。持っていれば降りる
    } else if (i < strategy.warmup) {
      pending = 0;                       // 計算に必要な本数がまだ溜まっていない
    } else if (dayBlocked) {
      pending = 0;                       // その日は打ち止め。降りるのは許すが新規は取らない
    } else {
      pending = signals[i] ? 1 : 0;
    }
  }

  // 最後の足の終値で、持っているものを畳んで成績を確定させる
  const last = candles[candles.length - 1];
  if (pos === 1 && units > 0) {
    const price = last.c * (1 - slip);
    const gross = units * price;
    const fee = gross * o.feeRate;
    cash += gross - fee;
    feesPaid += fee;
    if (entry) {
      const cost = entry.units * entry.price + entry.fee;
      trades.push({
        入り時刻: entry.t,
        出た時刻: last.t,
        入り値: entry.price,
        出た値: price,
        数量: entry.units,
        手数料: entry.fee + fee,
        損益: gross - fee - cost,
        損益率: (gross - fee - cost) / cost,
        強制手仕舞い: true,
      });
    }
    units = 0;
    pos = 0;
    equity[equity.length - 1] = { t: last.t, equity: cash, pos: 0 };
  }

  return {
    戦略: strategy.name,
    設定: { ...o, candles: undefined, strategy: undefined },
    開始資産: o.cash,
    最終資産: cash,
    手数料合計: feesPaid,
    停止した: halted,
    trades,
    equity,
    期間: { from: candles[0].t, to: last.t, 本数: candles.length },
  };
}
