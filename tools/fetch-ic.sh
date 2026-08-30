#!/usr/bin/env bash
# 全国のIC（入口・出口）の位置を OpenStreetMap から取り直して data/ic.tsv を作る。
# 新しいICが開通したとき、または収録漏れがあったときだけ実行すればよい。
# データは © OpenStreetMap contributors / ODbL。
set -eu

cd "$(dirname "$0")/.."
mkdir -p data

echo "OpenStreetMap から取得しています（1〜3分かかります）…"

QUERY='[out:csv(::lat,::lon,name,ref;false)][timeout:600];
area["ISO3166-1"="JP"][admin_level=2]->.a;
node(area.a)[highway=motorway_junction];
out;'

curl -s -m 600 --data-binary "$QUERY" \
  https://overpass-api.de/api/interpreter -o data/ic_raw.tsv

echo "整形しています…"

# 名前なし・JCT（乗り降りできない）・SA/PA を除き、同じ名前と番号の重複をまとめる。
awk -F'\t' '
  $3 == "" { next }
  $3 ~ /JCT|ジャンクション/ { next }
  $3 ~ /SA\(|PA\(|SA$|PA$|サービスエリア|パーキングエリア|BS$|バスストップ/ { next }
  {
    name = $3; ref = $4
    gsub(/\r/, "", name); gsub(/\r/, "", ref)
    lat = sprintf("%.4f", $1); lon = sprintf("%.4f", $2)
    key = name "\t" ref "\t" substr(lat, 1, 6) "\t" substr(lon, 1, 7)
    if (seen[key]++) next
    print name "\t" ref "\t" lat "\t" lon
  }
' data/ic_raw.tsv > data/ic.tsv

rm -f data/ic_raw.tsv
echo "data/ic.tsv を更新しました（$(wc -l < data/ic.tsv) 件）"
echo "続けて tools/build.sh を実行してください。"
