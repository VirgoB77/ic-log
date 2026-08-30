#!/usr/bin/env bash
# src/app.html の __IC_DB__ に data/ic.tsv を差し込んで、2つの成果物を作る。
#   index.html       … ブラウザで直接開ける単体ファイル
#   dist/artifact.html … Artifact 公開用（<!DOCTYPE>/<html>/<head>/<body> なしの断片）
set -eu

cd "$(dirname "$0")/.."
mkdir -p dist

if [ ! -f data/ic.tsv ]; then
  echo "data/ic.tsv がありません。tools/fetch-ic.sh を先に実行してください。" >&2
  exit 1
fi

# 1) Artifact 用の断片
awk '/__IC_DB__/{ while ((getline line < "data/ic.tsv") > 0) print line; next } { print }' \
  src/app.html > dist/artifact.html

# 2) 単体で開ける index.html（最初の </style> までを <head> に入れる）
awk '
BEGIN{
  print "<!DOCTYPE html>"
  print "<html lang=\"ja\">"
  print "<head>"
  print "<meta charset=\"utf-8\">"
  print "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">"
  print "<meta name=\"theme-color\" content=\"#0a6b3d\">"
  inhead = 1
}
{ print }
/<\/style>/ && inhead == 1 { print "</head>"; print "<body>"; inhead = 0 }
END{ print "</body>"; print "</html>" }
' dist/artifact.html > index.html

echo "できました:"
echo "  index.html          $(wc -c < index.html) バイト"
echo "  dist/artifact.html  $(wc -c < dist/artifact.html) バイト"
echo "  IC件数              $(wc -l < data/ic.tsv)"
