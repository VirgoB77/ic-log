// 取引所とのやり取り。
//
// 2種類ある。どちらも同じ形で使えるので、紙と実弾で本体のコードは変わらない。
//   PaperExchange  … 値段は本物、注文は嘘。お金は1円も動かない。
//   BitbankExchange … 本物。実弾。
//
// ⚠ 認証が要るAPI（残高照会・発注）は、作った環境から取引所へ通信できなかったため
//   一度も動かして確かめていない。実弾の前に必ず `node bot.mjs check` を通すこと。
//   あれは残高を読むだけの安全な呼び出しで、鍵と署名が正しいかをそこで確かめる。

import { createHmac } from 'node:crypto';
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { TIMEFRAMES, dedupe } from './candles.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const STATE_DIR = join(HERE, '..', 'state');

const PUBLIC_API = 'https://public.bitbank.cc';
const PRIVATE_API = 'https://api.bitbank.cc';

// --- 誰でも読める値段 -------------------------------------------------

export async function ticker(pair) {
  const res = await fetch(`${PUBLIC_API}/${pair}/ticker`);
  if (!res.ok) throw new Error(`現在値が取れない (${res.status})`);
  const body = await res.json();
  if (body?.success !== 1) throw new Error(`取引所がエラーを返した: ${JSON.stringify(body).slice(0, 200)}`);
  return {
    最終価格: Number(body.data.last),
    買値: Number(body.data.buy),
    売値: Number(body.data.sell),
  };
}

// 直近の足を、必要な本数ぶん集める。
// まだ終わっていない足は捨てる。途中の足で判断すると、値が動くたびに判断が変わってしまう。
export async function recentCandles(pair, tf, minBars) {
  const spec = TIMEFRAMES[tf];
  if (!spec) throw new Error(`知らない足の種類: ${tf}`);

  const out = [];
  const now = new Date();
  let 最後のしくじり = null;
  const 遡る上限 = spec.unit === 'year' ? 6 : 40; // 年 or 日
  for (let back = 0; back < 遡る上限 && out.length < minBars + 2; back++) {
    const d = new Date(now.getTime() - back * (spec.unit === 'year' ? 365 : 1) * 86_400_000);
    const key = spec.unit === 'year'
      ? String(d.getUTCFullYear())
      : `${d.getUTCFullYear()}${String(d.getUTCMonth() + 1).padStart(2, '0')}${String(d.getUTCDate()).padStart(2, '0')}`;
    try {
      const res = await fetch(`${PUBLIC_API}/${pair}/candlestick/${tf}/${key}`);
      if (!res.ok) { 最後のしくじり = `HTTP ${res.status}`; continue; }
      const body = await res.json();
      const rows = body?.data?.candlestick?.[0]?.ohlcv;
      if (!Array.isArray(rows)) { 最後のしくじり = `返ってきた形が想定と違う: ${JSON.stringify(body).slice(0, 150)}`; continue; }
      out.push(...rows.map((r) => ({
        t: Number(r[5]), o: Number(r[0]), h: Number(r[1]),
        l: Number(r[2]), c: Number(r[3]), v: Number(r[4]),
      })));
    } catch (e) {
      最後のしくじり = e.message; // その日ぶんが無いことはあるので、すぐには諦めない
    }
  }

  // 1本も取れなかったのに黙って空を返すと、呼んだ側が理由もわからず待ち続ける。
  if (out.length === 0) {
    throw new Error(
      `${pair} の ${tf} 足が1本も取れなかった。\n` +
      `  最後のしくじり: ${最後のしくじり ?? '理由不明'}\n` +
      '  通貨ペアの綴りと、取引所へ通信できるかを確かめること。',
    );
  }

  const 今 = Date.now();
  return dedupe(out).filter((k) => k.t + spec.ms <= 今); // 出来上がった足だけ
}

// --- 紙の取引所 -------------------------------------------------------

export class PaperExchange {
  constructor({ pair, cash = 300_000, feeRate = 0.0012, slippageBps = 5, stateFile }) {
    this.名前 = '紙トレード（お金は動かない）';
    this.実弾 = false;
    this.pair = pair;
    this.feeRate = feeRate;
    this.slip = slippageBps / 10_000;
    this.stateFile = stateFile ?? join(STATE_DIR, `paper_${pair}.json`);
    this.state = this.読み込む() ?? { jpy: cash, base: 0, 元手: cash, 履歴: [] };
  }

  読み込む() {
    if (!existsSync(this.stateFile)) return null;
    try { return JSON.parse(readFileSync(this.stateFile, 'utf8')); } catch { return null; }
  }

  保存() {
    if (!existsSync(STATE_DIR)) mkdirSync(STATE_DIR, { recursive: true });
    writeFileSync(this.stateFile, JSON.stringify(this.state, null, 2), 'utf8');
  }

  async balance() {
    return { jpy: this.state.jpy, base: this.state.base };
  }

  async buy(pair, 数量) {
    const t = await ticker(pair);
    const price = t.売値 * (1 + this.slip);
    const 代金 = 数量 * price;
    const 手数料 = 代金 * this.feeRate;
    if (代金 + 手数料 > this.state.jpy) throw new Error('残高が足りない（紙）');
    this.state.jpy -= 代金 + 手数料;
    this.state.base += 数量;
    this.state.履歴.push({ 時刻: Date.now(), 向き: '買', 数量, 値段: price, 手数料 });
    this.保存();
    return { 値段: price, 数量, 手数料 };
  }

  async sell(pair, 数量) {
    const t = await ticker(pair);
    const price = t.買値 * (1 - this.slip);
    const 代金 = 数量 * price;
    const 手数料 = 代金 * this.feeRate;
    if (数量 > this.state.base + 1e-12) throw new Error('持っていない数量を売ろうとした（紙）');
    this.state.jpy += 代金 - 手数料;
    this.state.base -= 数量;
    this.state.履歴.push({ 時刻: Date.now(), 向き: '売', 数量, 値段: price, 手数料 });
    this.保存();
    return { 値段: price, 数量, 手数料 };
  }
}

// --- 本物の取引所 -----------------------------------------------------

export class BitbankExchange {
  constructor({ key, secret }) {
    if (!key || !secret) throw new Error('APIキーが無い。.env を用意すること');
    this.名前 = 'bitbank（実弾）';
    this.実弾 = true;
    this.key = key;
    this.secret = secret;
  }

  // bitbank の認証。時刻と中身から署名を作って添える。
  署名(method, path, body) {
    const 時刻 = String(Date.now());
    const 有効幅 = '5000';
    const 元 = method === 'GET'
      ? 時刻 + 有効幅 + path
      : 時刻 + 有効幅 + body;
    return {
      'ACCESS-KEY': this.key,
      'ACCESS-REQUEST-TIME': 時刻,
      'ACCESS-TIME-WINDOW': 有効幅,
      'ACCESS-SIGNATURE': createHmac('sha256', this.secret).update(元).digest('hex'),
      'Content-Type': 'application/json',
    };
  }

  async 呼ぶ(method, path, params) {
    const body = method === 'POST' ? JSON.stringify(params ?? {}) : '';
    const 問い合わせ = method === 'GET' && params
      ? '?' + new URLSearchParams(params).toString()
      : '';
    const 全体 = path + 問い合わせ;
    const res = await fetch(PRIVATE_API + 全体, {
      method,
      headers: this.署名(method, 全体, body),
      body: method === 'POST' ? body : undefined,
    });
    const 中身 = await res.json().catch(() => null);
    if (中身?.success !== 1) {
      const コード = 中身?.data?.code;
      throw new Error(
        `取引所が受け付けなかった (HTTP ${res.status}${コード ? ` / code ${コード}` : ''}): ` +
        `${JSON.stringify(中身).slice(0, 300)}\n` +
        'code 20001〜20004 は鍵か署名の誤り。bitbank の最新API仕様を確認すること。',
      );
    }
    return 中身.data;
  }

  async balance() {
    const d = await this.呼ぶ('GET', '/v1/user/assets');
    const 表 = {};
    for (const a of d.assets ?? []) 表[a.asset] = Number(a.free_amount);
    return { jpy: 表.jpy ?? 0, 全部: 表 };
  }

  async 発注(pair, 向き, 数量) {
    return this.呼ぶ('POST', '/v1/user/spot/order', {
      pair,
      amount: String(数量),
      side: 向き,      // 'buy' or 'sell'
      type: 'market',
    });
  }

  async buy(pair, 数量) {
    const d = await this.発注(pair, 'buy', 数量);
    return { 値段: Number(d.average_price || 0), 数量: Number(d.start_amount || 数量), 注文番号: d.order_id };
  }

  async sell(pair, 数量) {
    const d = await this.発注(pair, 'sell', 数量);
    return { 値段: Number(d.average_price || 0), 数量: Number(d.start_amount || 数量), 注文番号: d.order_id };
  }
}
