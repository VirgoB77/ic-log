// 成績の集計と表示。
//
// ここは「よく見せない」ことだけを考えて書いてある。
// 手数料を引いた後の数字しか出さないし、買って持ちっぱなしに負けていれば
// はっきりそう書く。都合の良い数字だけ並べたら、損をするのは自分になる。

export function metrics(result) {
  const { trades, equity } = result;
  const 純損益 = result.最終資産 - result.開始資産;

  const 勝ち = trades.filter((t) => t.損益 > 0);
  const 負け = trades.filter((t) => t.損益 <= 0);
  const 総利益 = 勝ち.reduce((s, t) => s + t.損益, 0);
  const 総損失 = Math.abs(負け.reduce((s, t) => s + t.損益, 0));

  // 最大ドローダウン … 資産の山からどれだけ落ち込んだかの最大値
  let peak = -Infinity;
  let maxDD = 0;
  for (const e of equity) {
    peak = Math.max(peak, e.equity);
    if (peak > 0) maxDD = Math.max(maxDD, (peak - e.equity) / peak);
  }

  // 足ごとの騰落からシャープレシオを出し、年率に直す
  const rets = [];
  for (let i = 1; i < equity.length; i++) {
    const prev = equity[i - 1].equity;
    if (prev > 0) rets.push(equity[i].equity / prev - 1);
  }
  const 平均 = rets.length ? rets.reduce((a, b) => a + b, 0) / rets.length : 0;
  const 分散 = rets.length > 1
    ? rets.reduce((s, r) => s + (r - 平均) ** 2, 0) / (rets.length - 1)
    : 0;
  const 標準偏差 = Math.sqrt(分散);
  const 日数 = Math.max(1, (result.期間.to - result.期間.from) / 86_400_000);
  const 年あたりの本数 = (equity.length / 日数) * 365;
  const シャープ = 標準偏差 > 0 ? (平均 / 標準偏差) * Math.sqrt(年あたりの本数) : 0;

  const 年数 = 日数 / 365;
  const 年率 = 年数 > 0 && result.開始資産 > 0
    ? (result.最終資産 / result.開始資産) ** (1 / 年数) - 1
    : 0;

  const 持っていた本数 = equity.filter((e) => e.pos === 1).length;

  return {
    純損益,
    損益率: 純損益 / result.開始資産,
    年率,
    取引回数: trades.length,
    勝率: trades.length ? 勝ち.length / trades.length : 0,
    平均利益: 勝ち.length ? 総利益 / 勝ち.length : 0,
    平均損失: 負け.length ? 総損失 / 負け.length : 0,
    プロフィットファクター: 総損失 > 0 ? 総利益 / 総損失 : (総利益 > 0 ? Infinity : 0),
    最大ドローダウン: maxDD,
    シャープ,
    手数料合計: result.手数料合計,
    手数料の重み: Math.abs(純損益) > 0 ? result.手数料合計 / Math.abs(純損益) : Infinity,
    持っていた割合: equity.length ? 持っていた本数 / equity.length : 0,
  };
}

const 円 = (n) => `${Math.round(n).toLocaleString('ja-JP')}円`;
const 割 = (n) => `${(n * 100).toFixed(2)}%`;
const 日 = (t) => new Date(t).toISOString().slice(0, 10);

export function formatReport(result, benchmark = null) {
  const m = metrics(result);
  const L = [];
  const line = (s = '') => L.push(s);

  line('');
  line('━'.repeat(56));
  line(`  ${result.戦略}`);
  line(`  ${日(result.期間.from)} 〜 ${日(result.期間.to)}（${result.期間.本数}本）`);
  line('━'.repeat(56));
  line('');
  line(`  元手      ${円(result.開始資産)}`);
  line(`  最終      ${円(result.最終資産)}`);
  line(`  損益      ${純損益表示(m.純損益)}（${割(m.損益率)}／年率 ${割(m.年率)}）`);
  line('');
  line(`  取引回数  ${m.取引回数}回`);
  line(`  勝率      ${割(m.勝率)}`);
  line(`  平均利益  ${円(m.平均利益)}`);
  line(`  平均損失  ${円(m.平均損失)}`);
  line(`  PF        ${m.プロフィットファクター === Infinity ? '∞' : m.プロフィットファクター.toFixed(2)}（1を割ったら負け越し）`);
  line('');
  line(`  最大下落  ${割(m.最大ドローダウン)}  ← 途中でここまで減る`);
  line(`  シャープ  ${m.シャープ.toFixed(2)}`);
  line(`  持ち時間  ${割(m.持っていた割合)}`);
  line(`  手数料    ${円(m.手数料合計)}`);
  line('');

  // ここから下は、都合の悪いことを書く場所。
  const 警告 = [];

  if (benchmark) {
    const b = metrics(benchmark);
    line('─'.repeat(56));
    line(`  買って持ちっぱなしなら … ${円(benchmark.最終資産)}（${割(b.損益率)}）`);
    const 差 = result.最終資産 - benchmark.最終資産;
    line(`  この戦略との差         … ${純損益表示(差)}`);
    line('');
    if (差 <= 0) {
      警告.push(
        '買って持ちっぱなしに負けている。手間と手数料をかけて成績を悪くしているだけなので、この設定を実弾で回す理由はない。',
      );
    }
    if (b.最大ドローダウン > 0 && m.最大ドローダウン > b.最大ドローダウン && 差 <= 0) {
      警告.push('しかも持ちっぱなしより下落が深い。リターンもリスクも負けている。');
    }
  }

  if (m.取引回数 < 30) {
    警告.push(
      `取引回数が${m.取引回数}回しかない。この程度の回数では、成績が良くても偶然と区別がつかない。期間を延ばすか足を短くして、最低でも30回は見ること。`,
    );
  }
  if (m.手数料の重み > 0.5 && Number.isFinite(m.手数料の重み)) {
    警告.push(`手数料が損益の${割(m.手数料の重み)}を占めている。売買しすぎ。`);
  }
  if (m.最大ドローダウン > 0.4) {
    警告.push(
      `途中で${割(m.最大ドローダウン)}減る。元手${円(result.開始資産)}なら一時${円(result.開始資産 * m.最大ドローダウン)}のマイナスに耐える必要がある。耐えられないなら金額を下げること。`,
    );
  }
  if (result.停止した) {
    警告.push('下落上限に当たって途中で売買を止めている。上の成績はその停止込みの数字。');
  }

  if (警告.length) {
    line('─'.repeat(56));
    line('  ⚠ 読むべきところ');
    for (const w of 警告) line(`   ・${w}`);
    line('');
  }

  line('─'.repeat(56));
  line('  これは過去データ上の結果であって、明日そうなる保証はない。');
  line('  同じ数字が実弾で出ることはまずない、と思っておくこと。');
  line('');

  return L.join('\n');
}

function 純損益表示(n) {
  const s = 円(Math.abs(n));
  return n >= 0 ? `+${s}` : `-${s}`;
}

// 複数の設定をまとめて比べるときの一覧表。
export function formatTable(rows) {
  const head = ['戦略', '最終資産', '損益率', '取引', '勝率', '最大下落', 'PF'];
  const body = rows.map((r) => {
    const m = metrics(r);
    return [
      r.戦略,
      円(r.最終資産),
      割(m.損益率),
      `${m.取引回数}回`,
      割(m.勝率),
      割(m.最大ドローダウン),
      m.プロフィットファクター === Infinity ? '∞' : m.プロフィットファクター.toFixed(2),
    ];
  });
  const all = [head, ...body];
  const w = head.map((_, i) => Math.max(...all.map((r) => 幅(r[i]))));
  const 行 = (r) => '  ' + r.map((c, i) => c + ' '.repeat(w[i] - 幅(c))).join('  ');
  return ['', 行(head), '  ' + '─'.repeat(w.reduce((a, b) => a + b + 2, 0)), ...body.map(行), ''].join('\n');
}

// 全角は2文字ぶんの幅で数える
function 幅(s) {
  let n = 0;
  for (const ch of String(s)) n += /[　-鿿！-｠]/.test(ch) ? 2 : 1;
  return n;
}
