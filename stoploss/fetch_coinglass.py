#!/usr/bin/env python3
"""Coinglass の API から清算などの履歴を取り、stoploss/data/liq/ にためる。

GitHub Actions で動かす前提。鍵（COINGLASS_API_KEY）は GitHub の Secrets に入れておく。
鍵が無いときは何もせずに終わる（エラーにしない）。

やること
  - 決めた窓口（DATASETS）ごとに、新しい方から古い方へさかのぼって全部取る
  - 返ってきた項目は名前を変えずにそのまま CSV に残す（時刻だけ読みやすく直す）
  - 1ページ目の生の返事を raw/ に保存しておく（項目名を確かめるため）
  - 2回目からは、前回の続きだけ取る

使い方
  COINGLASS_API_KEY=xxxx python3 fetch_coinglass.py [--start 2020-01-01] [--only aggregated_liq_1h]
"""
import argparse, datetime as dt, json, os, sys, time
import pandas as pd
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "liq")
RAW = os.path.join(OUT, "raw")
os.makedirs(RAW, exist_ok=True)

BASE = os.environ.get("COINGLASS_BASE_URL", "https://open-api-v4.coinglass.com")
KEY = os.environ.get("COINGLASS_API_KEY", "").strip()
RPM = float(os.environ.get("COINGLASS_RPM", "20"))      # 1分あたりの回数の上限（プランによる）。控えめに
PAGE_LIMIT = int(os.environ.get("COINGLASS_LIMIT", "1000"))
STATE = os.path.join(OUT, "coinglass_state.json")

# 取りに行く窓口。path / params / 返ってくる項目名は Coinglass 公式の説明書（coinglass-official/coinglass-api-docs）に合わせた。
#   全取引所合計の清算: /api/futures/liquidation/aggregated-history  項目 time(ミリ秒), aggregated_long_liquidation_usd, aggregated_short_liquidation_usd
#   取引所ごとの清算:   /api/futures/liquidation/history             項目 time, long_liquidation_usd, short_liquidation_usd
#   建玉:               /api/futures/open-interest/aggregated-history 項目 time, open, high, low, close
# interval は「1本が何時間か」。プランで取れる細かさと長さが決まる:
#   Hobbyist(月29ドル): 4h以上。4hは直近180日、1dは全期間
#   Startup(月79ドル):  30m以上。1hは直近180日、1dは全期間
#   Standard 以上:      1hで360〜720日
# 取れないものはエラーとして記録して飛ばす（全体は止めない）。
# exchange_list は起動時に /api/futures/supported-exchanges から作る（下の EXCHANGES は取れなかったときの予備）。
EXCHANGES = "Binance,OKX,Bybit,Bitget,Gate,HTX,Bitmex,Bitfinex,Kraken,Coinbase,dYdX,KuCoin,CoinEx,BingX,Deribit"
DATASETS = [
    {"name": "aggregated_liq_1d", "path": "/api/futures/liquidation/aggregated-history",
     "params": {"symbol": "BTC", "interval": "1d", "exchange_list": "@ALL"}, "interval_sec": 86400,
     "note": "全取引所合計の清算・日足（どのプランでも全期間）"},
    {"name": "aggregated_liq_4h", "path": "/api/futures/liquidation/aggregated-history",
     "params": {"symbol": "BTC", "interval": "4h", "exchange_list": "@ALL"}, "interval_sec": 14400,
     "note": "全取引所合計の清算・4時間足（Hobbyist で直近180日）"},
    {"name": "aggregated_liq_1h", "path": "/api/futures/liquidation/aggregated-history",
     "params": {"symbol": "BTC", "interval": "1h", "exchange_list": "@ALL"}, "interval_sec": 3600,
     "note": "全取引所合計の清算・1時間足（Startup 以上。Hobbyist では取れない）"},
    {"name": "binance_btcusdt_liq_1d", "path": "/api/futures/liquidation/history",
     "params": {"exchange": "Binance", "symbol": "BTCUSDT", "interval": "1d"}, "interval_sec": 86400,
     "note": "Binance BTCUSDT だけの清算・日足"},
    {"name": "aggregated_oi_1d", "path": "/api/futures/open-interest/aggregated-history",
     "params": {"symbol": "BTC", "interval": "1d", "unit": "usd"}, "interval_sec": 86400,
     "note": "全取引所合計の建玉・日足"},
    {"name": "aggregated_oi_4h", "path": "/api/futures/open-interest/aggregated-history",
     "params": {"symbol": "BTC", "interval": "4h", "unit": "usd"}, "interval_sec": 14400,
     "note": "全取引所合計の建玉・4時間足"},
]

_last_call = 0.0


def call(path, params):
    """1回呼ぶ。回数制限を守り、失敗したら少し待って数回やり直す。"""
    global _last_call
    wait = 60.0 / RPM - (time.time() - _last_call)
    if wait > 0:
        time.sleep(wait)
    headers = {"CG-API-KEY": KEY, "accept": "application/json"}
    for i in range(4):
        _last_call = time.time()
        try:
            r = requests.get(BASE + path, params=params, headers=headers, timeout=60)
        except requests.RequestException as e:
            print(f"  ! 通信に失敗 ({e})。待ってやり直す")
            time.sleep(5 * (i + 1))
            continue
        if r.status_code == 429:
            print("  ! 回数制限にかかった。60秒待つ")
            time.sleep(60)
            continue
        if r.status_code >= 500:
            time.sleep(5 * (i + 1))
            continue
        try:
            body = r.json()
        except ValueError:
            body = {"_http": r.status_code, "_text": r.text[:500]}
        return r.status_code, body
    return None, None


def unwrap(body):
    """返事の入れ物をはがして、記録のリストと「成功か」を返す。"""
    if not isinstance(body, dict):
        return [], False, "返事が辞書の形ではない"
    code = str(body.get("code", body.get("status", "")))
    ok = body.get("success", None)
    if ok is None:
        ok = code in ("0", "200", "")
    data = body.get("data", [])
    if isinstance(data, dict):
        for k in ("list", "data", "records", "items"):
            if isinstance(data.get(k), list):
                data = data[k]
                break
    if not isinstance(data, list):
        data = []
    return data, bool(ok), body.get("msg") or body.get("message") or ""


def to_time(v):
    """time の値（秒でもミリ秒でも文字でも）を日時にする。"""
    try:
        x = float(v)
    except (TypeError, ValueError):
        return pd.to_datetime(v, errors="coerce")
    if x > 1e14:
        x /= 1e6
    elif x > 1e11:
        x /= 1e3
    return pd.to_datetime(x, unit="s", errors="coerce")


def time_key(rec):
    for k in ("time", "t", "timestamp", "ts", "create_time", "createTime", "date"):
        if k in rec:
            return k
    return None


def fetch_dataset(ds, start_dt, state):
    name = ds["name"]
    path = os.path.join(OUT, f"coinglass_{name}.csv")
    have = pd.read_csv(path, parse_dates=["time"]) if os.path.exists(path) else None
    # どこまでさかのぼるか。すでに持っていれば、その続きだけ（念のため少し重ねる）
    lower = start_dt
    if have is not None and len(have):
        lower = max(start_dt, have["time"].max() - pd.Timedelta(seconds=ds["interval_sec"] * 3))
    end = int(time.time())
    pages, rows, seen = 0, [], set()
    err = None
    while True:
        params = dict(ds["params"], limit=PAGE_LIMIT, end_time=end * 1000, start_time=int(lower.timestamp()) * 1000)
        status, body = call(ds["path"], params)
        if body is None:
            err = "通信に失敗し続けた"; break
        if pages == 0:
            # 項目名を確かめるための見本。大きくならないよう、記録は先頭5件だけ残す
            sample = body
            if isinstance(body, dict) and isinstance(body.get("data"), list):
                sample = dict(body, data=body["data"][:5], _data_count=len(body["data"]))
            with open(os.path.join(RAW, f"coinglass_{name}_page1.json"), "w") as f:
                json.dump({"request": {"path": ds["path"], "params": {k: v for k, v in params.items()}}, "status": status, "body": sample}, f, ensure_ascii=False, indent=1)
        data, ok, msg = unwrap(body)
        if status != 200 or not ok:
            hint = {401: "鍵がちがう（COINGLASS_API_KEY を確かめる）", 403: "いまのプランでは取れない窓口か細かさ",
                    400: "パラメータがおかしい", 422: "パラメータは正しいが受け付けられない（プランの範囲外など）",
                    429: "回数制限"}.get(status, "")
            err = f"HTTP {status} {hint}: {msg or json.dumps(body, ensure_ascii=False)[:300]}"; break
        if not data:
            break
        tk = time_key(data[0])
        if tk is None:
            err = f"時刻の項目が見つからない。項目: {list(data[0].keys())}"; break
        oldest = None
        added = 0
        for rec in data:
            t = to_time(rec.get(tk))
            if pd.isna(t):
                continue
            key = int(t.timestamp())
            if key in seen:
                continue
            seen.add(key); added += 1
            rows.append(dict(rec, time=t))
            oldest = t if oldest is None or t < oldest else oldest
        pages += 1
        print(f"  {name}: ページ {pages}, {len(data)} 件 (新しく {added}), いちばん古い {oldest}")
        if added == 0 or oldest is None or oldest <= lower or len(data) < PAGE_LIMIT:
            break
        end = int(oldest.timestamp()) - 1
        if pages >= 400:
            print("  ! ページが多すぎるので打ち切り"); break
    st = state.setdefault(name, {})
    st["last_run"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    st["last_error"] = err
    if err:
        print(f"  ! {name}: {err}")
    if rows:
        new = pd.DataFrame(rows)
        new = new[["time"] + [c for c in new.columns if c != "time"]]
        if have is not None:
            new = pd.concat([have, new])
        new = new.drop_duplicates("time", keep="last").sort_values("time")
        new.to_csv(path, index=False)
        st["rows"] = int(len(new)); st["first"] = str(new["time"].iloc[0]); st["last"] = str(new["time"].iloc[-1])
        print(f"{name}: 合計 {len(new)} 件, {new['time'].iloc[0]} 〜 {new['time'].iloc[-1]} -> {os.path.basename(path)}")
    else:
        print(f"{name}: 新しいものは無かった")
    return err


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2020-01-01")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    if not KEY:
        print("COINGLASS_API_KEY が無いので、Coinglass からは取らない（GitHub の Secrets に入れると動く）")
        return 0
    start_dt = pd.Timestamp(a.start)
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    # いまのプランを確かめて記録する（取れないものの理由が分かるように）
    status, body = call("/api/user/account/subscription", {})
    plan = (body or {}).get("data") if isinstance(body, dict) else None
    if status == 401:
        print("鍵がちがうと言われた（HTTP 401）。GitHub の Secrets の COINGLASS_API_KEY を確かめる")
        return 1
    print(f"プラン: {plan}")
    state["plan"] = plan
    # 取引所の一覧を取って、全取引所合計に使う名前を作る
    status, body = call("/api/futures/supported-exchanges", {})
    names = (body or {}).get("data") if isinstance(body, dict) else None
    if isinstance(names, list) and names and all(isinstance(x, str) for x in names):
        exchange_list = ",".join(names)
        print(f"取引所 {len(names)} 社: {exchange_list}")
    else:
        exchange_list = EXCHANGES
        print(f"取引所の一覧が取れなかったので予備の一覧を使う: {exchange_list}")
    state["exchange_list"] = exchange_list
    for ds in DATASETS:
        if ds["params"].get("exchange_list") == "@ALL":
            ds["params"]["exchange_list"] = exchange_list
    errors = {}
    for ds in DATASETS:
        if a.only and ds["name"] != a.only:
            continue
        print(f"== {ds['name']}  {ds.get('note', '')}\n   {ds['path']} {ds['params']}")
        e = fetch_dataset(ds, start_dt, state)
        if e:
            errors[ds["name"]] = e
        json.dump(state, open(STATE, "w"), ensure_ascii=False, indent=1)
    if errors:
        print("\n取れなかったもの:")
        for k, v in errors.items():
            print(f"  {k}: {v}")
        # 全部だめなら失敗にする（鍵やプランの問題に気づけるように）
        if len(errors) == len([d for d in DATASETS if not a.only or d["name"] == a.only]):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
