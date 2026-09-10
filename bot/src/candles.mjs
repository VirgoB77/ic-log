// ローソク足の取得・読み込み・生成。
//
// 足の形は全部これで統一する:
//   { t: 開始時刻(ミリ秒), o: 始値, h: 高値, l: 安値, c: 終値, v: 出来高 }
//
// 並びは必ず「古い順」。エンジンはこれを前提にしている。

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
export const CACHE_DIR = join(HERE, '..', 'data');

// bitbank の公開API。鍵は要らない。
const PUBLIC_API = 'https://public.bitbank.cc';

// 足の種類。bitbank の指定に合わせている。
// 1day 以上は年(YYYY)単位、それより短いものは日(YYYYMMDD)単位でしか取れない。
export const TIMEFRAMES = {
  '1min': { ms: 60_000, unit: 'day' },
  '5min': { ms: 300_000, unit: 'day' },
  '15min': { ms: 900_000, unit: 'day' },
  '30min': { ms: 1_800_000, unit: 'day' },
  '1hour': { ms: 3_600_000, unit: 'day' },
  '4hour': { ms: 14_400_000, unit: 'year' },
  '8hour': { ms: 28_800_000, unit: 'year' },
  '12hour': { ms: 43_200_000, unit: 'year' },
  '1day': { ms: 86_400_000, unit: 'year' },
  '1week': { ms: 604_800_000, unit: 'year' },
};

// --- 取引所から取る ---------------------------------------------------

// bitbank は 1回のリクエストで「1年分」か「1日分」しか返さない。
// 期間をまたぐときは複数回に分けて呼び、つなげる。
export async function fetchCandles(pair, tf, from, to) {
  const spec = TIMEFRAMES[tf];
  if (!spec) throw new Error(`知らない足の種類: ${tf}`);

  const keys = spec.unit === 'year' ? yearKeys(from, to) : dayKeys(from, to);
  const all = [];
  for (const key of keys) {
    const chunk = await fetchOneChunk(pair, tf, key);
    all.push(...chunk);
  }
  return dedupe(all).filter((k) => k.t >= from.getTime() && k.t <= to.getTime());
}

async function fetchOneChunk(pair, tf, key) {
  const url = `${PUBLIC_API}/${pair}/candlestick/${tf}/${key}`;
  const res = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!res.ok) throw new Error(`取得に失敗した (${res.status}): ${url}`);
  const body = await res.json();

  // 取引所が仕様を変えたときに黙って空を返さないよう、形を確かめる。
  if (body?.success !== 1) {
    throw new Error(`取引所がエラーを返した: ${JSON.stringify(body).slice(0, 200)}`);
  }
  const rows = body?.data?.candlestick?.[0]?.ohlcv;
  if (!Array.isArray(rows)) {
    throw new Error(
      `返ってきた形が想定と違う。取引所のAPI仕様を確認すること。\n受け取ったもの: ${JSON.stringify(body).slice(0, 300)}`,
    );
  }
  // ohlcv の並びは [始値, 高値, 安値, 終値, 出来高, 開始時刻ミリ秒]。文字列で来る。
  return rows.map((r) => ({
    t: Number(r[5]),
    o: Number(r[0]),
    h: Number(r[1]),
    l: Number(r[2]),
    c: Number(r[3]),
    v: Number(r[4]),
  }));
}

function yearKeys(from, to) {
  const out = [];
  for (let y = from.getUTCFullYear(); y <= to.getUTCFullYear(); y++) out.push(String(y));
  return out;
}

function dayKeys(from, to) {
  const out = [];
  const d = new Date(Date.UTC(from.getUTCFullYear(), from.getUTCMonth(), from.getUTCDate()));
  while (d.getTime() <= to.getTime()) {
    out.push(
      `${d.getUTCFullYear()}${String(d.getUTCMonth() + 1).padStart(2, '0')}${String(d.getUTCDate()).padStart(2, '0')}`,
    );
    d.setUTCDate(d.getUTCDate() + 1);
  }
  return out;
}

// 同じ時刻の足が二重に入らないようにして、古い順に並べ直す。
export function dedupe(candles) {
  const byTime = new Map();
  for (const k of candles) {
    if (Number.isFinite(k.t) && Number.isFinite(k.c)) byTime.set(k.t, k);
  }
  return [...byTime.values()].sort((a, b) => a.t - b.t);
}

// --- キャッシュ -------------------------------------------------------

export function cachePath(pair, tf) {
  return join(CACHE_DIR, `${pair}_${tf}.json`);
}

export function saveCache(pair, tf, candles) {
  if (!existsSync(CACHE_DIR)) mkdirSync(CACHE_DIR, { recursive: true });
  writeFileSync(cachePath(pair, tf), JSON.stringify(candles), 'utf8');
}

export function loadCache(pair, tf) {
  const p = cachePath(pair, tf);
  if (!existsSync(p)) return null;
  return dedupe(JSON.parse(readFileSync(p, 'utf8')));
}

// --- CSV から読む -----------------------------------------------------

// 株や為替のデータを外から持ってくるとき用。
// 1行目は見出し。日付,始値,高値,安値,終値,出来高 の順（英語見出しでも動く）。
export function loadCsv(path) {
  const text = readFileSync(path, 'utf8').trim();
  const lines = text.split(/\r?\n/);
  const out = [];
  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(',').map((s) => s.trim());
    if (cols.length < 5) continue;
    const t = Date.parse(cols[0]);
    if (Number.isNaN(t)) continue;
    const num = (s) => Number(String(s).replace(/[",]/g, ''));
    out.push({
      t,
      o: num(cols[1]),
      h: num(cols[2]),
      l: num(cols[3]),
      c: num(cols[4]),
      v: cols[5] === undefined ? 0 : num(cols[5]),
    });
  }
  return dedupe(out);
}

// --- 検算用のニセ相場 -------------------------------------------------

// エンジンが正しく動くか確かめるための、決まった種から作る作り物の値動き。
// 毎回まったく同じ並びになるので、テストの結果がぶれない。
export function synthCandles({ bars = 500, start = 1_000_000, drift = 0.0002, vol = 0.02, seed = 42 } = {}) {
  let s = seed >>> 0;
  const rand = () => {
    // xorshift32。外部ライブラリを使わずに毎回同じ乱数列を出すため。
    s ^= s << 13; s >>>= 0;
    s ^= s >> 17;
    s ^= s << 5; s >>>= 0;
    return s / 4_294_967_296;
  };

  const out = [];
  let price = start;
  const t0 = Date.UTC(2020, 0, 1);
  for (let i = 0; i < bars; i++) {
    const open = price;
    const step = drift + (rand() - 0.5) * 2 * vol;
    const close = Math.max(1, open * (1 + step));
    const high = Math.max(open, close) * (1 + rand() * vol * 0.5);
    const low = Math.min(open, close) * (1 - rand() * vol * 0.5);
    out.push({ t: t0 + i * 86_400_000, o: open, h: high, l: low, c: close, v: 1 + rand() });
    price = close;
  }
  return out;
}
