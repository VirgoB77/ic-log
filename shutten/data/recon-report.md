# 大店立地法 届出ページ 偵察レポート（2026-09-13）

**まとめ: Excel 2件 / PDF 19件 / わからない 42件 / 表 64件**

「そのページが機械で読める形か」だけを見ている。
判定が **表** か **Excel** なら自動化しやすい。**PDF** なら一手間、
**わからない** なら自分の目で見に行く必要がある。

### 兵庫県 大規模小売店舗立地法 縦覧状況

- URL: https://web.pref.hyogo.lg.jp/ks21/wd24_000000018.html
- メモ: 本命。縦覧中の案件が並ぶ。届出ごとの「資料」PDF 44本のうち2MB以下の33本を取った。ただし33本中32本は紙をスキャンした画像で文字が入っておらず、機械では読めない（2026-09-12確認）。読むならOCRが要る。保存はしてあるので、いまは表の3項目（届出日・店名・縦覧期間）だけを使う。2026-09-12から8MB級も取る（上限12MB）。読むにはOCRが要るので別の仕組みで。いま縦覧中の分しか載らないので、Wayback Machine の月1回の保存から過去分を積み直す（wayback.py、2026-09-12〜）。2019〜2023年のページは一覧を todokede_jyuuranYYMMDD.pdf に置いていたので、その PDF もアーカイブから前方一致で拾う
- robots.txt: 許可
- HTTP 200 / utf-8 / 35,293 バイト
- **判定: 表**
- 表 3 個 / PDFリンク 44 本 / Excel 0 本
- いちばん大きい表: 34 行 × 4 列
  - 見出しらしき行: 届出年月日 | 店舗名称 | 縦覧期間 | 概要
  - PDF: （PDF：142KB） → https://web.pref.hyogo.lg.jp/ks21/documents/onlinechirashi.pdf
  - PDF: 資料（PDF：8,057KB） → https://web.pref.hyogo.lg.jp/ks21/documents/freshbazaarinagawaten.pdf
  - PDF: 資料（PDF：6,162KB） → https://web.pref.hyogo.lg.jp/ks21/documents/drugcosmoskamitenoten.pdf
  - PDF: 資料（PDF：7,517KB） → https://web.pref.hyogo.lg.jp/ks21/documents/takaradushikaisoshikeikaku.pdf
  - PDF: 資料（PDF：8,845KB） → https://web.pref.hyogo.lg.jp/ks21/documents/maxvalueyasuda.pdf
- 出てきた言葉: 新設 / 変更 / 縦覧 / 届出
- 年度らしき表記: 令和8年 / 令和9年

### 兵庫県 大規模小売店舗立地法（案内）

- URL: https://web.pref.hyogo.lg.jp/ks21/r03_daitennrittihou.html
- メモ: 手引と様式のページ。過去分の一覧が別にぶら下がっていないか確かめる用
- robots.txt: 許可
- HTTP 200 / utf-8 / 23,277 バイト
- **判定: Excel**
- 表 0 個 / PDFリンク 8 本 / Excel 1 本
  - PDF: 手続の流れ（PDF：91KB） → https://web.pref.hyogo.lg.jp/ks21/documents/tetuduki011121.pdf
  - PDF: 詳細（PDF：142KB） → https://web.pref.hyogo.lg.jp/ks21/documents/onlinechirashi.pdf
  - PDF: 大規模小売店舗を設置する者が配慮すべき事項に関する指針（PDF：92KB） → https://web.pref.hyogo.lg.jp/ks21/documents/sisin_saikaitei.pdf
  - PDF: 主要鉄道駅近郊の商業地区における駐車場必要台数の自動車分担率に係る基準（PDF：60KB） → https://web.pref.hyogo.lg.jp/ks21/documents/buntanritu.pdf
  - PDF: 大規模小売店舗立地法に係る届出の手引（令和8年2月）（PDF：9,612KB） → https://web.pref.hyogo.lg.jp/ks21/documents/tebiki0802.pdf
  - Excel: 駐車場法チェックリスト（エクセル：20KB） → https://web.pref.hyogo.lg.jp/ks21/documents/parkinglawcl260511.xlsx
- 出てきた言葉: 新設 / 変更 / 廃止 / 縦覧 / 届出 / 店舗面積 / 開店
- 年度らしき表記: 令和7年 / 令和8年

### 神戸市 大規模小売店舗立地法 届出状況等

- URL: https://www.city.kobe.lg.jp/a31812/business/sangyoshinko/shokogyo/koritenporitchi/daitenhp/index.html
- メモ: 政令市なので県とは別に受理。「届出書」PDF 16本を取ったが、様式に1文字ずつ置かれた形で表としては読めない（2026-09-12確認）。保存はしてあるので、いまは表の項目だけを使う。2026-09-12から8MB級も取る（上限12MB）。読むにはOCRが要るので別の仕組みで。いま縦覧中の分しか載らないので、Wayback Machine の月1回の保存から過去分を積み直す（wayback.py、2026-09-12〜）
- robots.txt: 許可
- HTTP 200 / UTF-8 / 38,704 バイト
- **判定: 表**
- 表 12 個 / PDFリンク 20 本 / Excel 0 本
- いちばん大きい表: 43 行 × 5 列
  - 見出しらしき行: 届出日 | 店舗名称 | 縦覧期間 | 届出概要
  - PDF: 届出書（PDF：7,714KB） → https://www.city.kobe.lg.jp/documents/10974/todoke1141.pdf
  - PDF: 交通資料（PDF：3,534KB） → https://www.city.kobe.lg.jp/documents/10974/koutsu1141.pdf
  - PDF: 騒音資料（PDF：9,376KB） → https://www.city.kobe.lg.jp/documents/10974/souon1141.pdf
  - PDF: 届出書（PDF：512KB） → https://www.city.kobe.lg.jp/documents/10974/todoke1152.pdf
  - PDF: 届出書（PDF：175KB） → https://www.city.kobe.lg.jp/documents/10974/todoke1151.pdf
- 出てきた言葉: 縦覧 / 届出

### 尼崎市 大規模小売店舗立地法

- URL: https://www.city.amagasaki.hyogo.jp/sangyo/kigyou/kouri/069rittihou.html
- メモ: 一覧を持っていなかった。兵庫県のページへ外部リンクしているだけ（2026-09-11の保存ページで確認）。中規模小売店舗の届出は別にあるので、そちらは別途調べる
- **結果: 取りに行かなかった（一覧を持っていなかった。兵庫県のページへ外部リンクしているだけ（2026-09-11の保存ページで確認）。中規模小売店舗の届出は別にあるので、そちらは別途調べる）**

### 姫路市 中規模小売店舗の設置

- URL: https://www.city.himeji.lg.jp/sangyo/0000005793.html
- メモ: 中規模小売店舗の要綱と様式はあるが、届出された店の一覧は公開していなかった（2026-09-11の保存ページで確認）
- **結果: 取りに行かなかった（中規模小売店舗の要綱と様式はあるが、届出された店の一覧は公開していなかった（2026-09-11の保存ページで確認））**

### 大阪府 大規模小売店舗立地法

- URL: https://www.pref.osaka.lg.jp/o110060/shogyoshien/daikibokouritenpo/index.html
- メモ: 本命。2026年4月に手続きがオンライン化し、縦覧も府のHPで見られるようになった
- robots.txt: 許可
- HTTP 200 / utf-8 / 29,157 バイト
- **判定: 表**
- 表 1 個 / PDFリンク 18 本 / Excel 17 本
- いちばん大きい表: 8 行 × 2 列
  - 見出しらしき行: 地域名 | 移譲市町村
  - PDF: ［PDFファイル／524KB → https://www.pref.osaka.lg.jp/documents/7546/onlinekaishitirashi.pdf
  - PDF: PDFファイル／460KB → https://www.pref.osaka.lg.jp/documents/7546/shinsetsu_12-r5.pdf
  - PDF: PDFファイル／538KB → https://www.pref.osaka.lg.jp/documents/7546/r710-5-1_r6.pdf
  - PDF: PDFファイル／410KB → https://www.pref.osaka.lg.jp/documents/7546/r803-5-1.pdf
  - PDF: PDFファイル／386KB → https://www.pref.osaka.lg.jp/documents/7546/r806-5-1.pdf
  - Excel: エクセルファイル／58KB → https://www.pref.osaka.lg.jp/documents/7546/shinsetsu_12-r5.xlsx
  - Excel: エクセルファイル／32KB → https://www.pref.osaka.lg.jp/documents/7546/r710-5-1_r6.xlsx
  - Excel: エクセルファイル／28KB → https://www.pref.osaka.lg.jp/documents/7546/r803-5-1_1.xlsx
  - Excel: エクセルファイル／26KB → https://www.pref.osaka.lg.jp/documents/7546/r806-5-1.xlsx
  - Excel: エクセルファイル／100KB → https://www.pref.osaka.lg.jp/documents/7546/husoku_12-r5.xls
- 出てきた言葉: 新設 / 変更 / 廃止 / 縦覧 / 届出 / 店舗面積
- 年度らしき表記: 令和4年 / 令和5年 / 令和6年 / 令和7年 / 令和8年 / 平成12年 / 平成13年

### 大阪市 大規模小売店舗立地法 手続き・届出

- URL: https://www.city.osaka.lg.jp/keizaisenryaku/page/0000373985.html
- メモ: Excel 3本。サーバーがこの仕組みからの取得に404を返す（ブラウザからは落とせる）。参照元ヘッダー、ページを先に開いてクッキーを持つ経路、どちらも404のまま（2026-09-12に確認）。名乗りを偽って取る手は使わない。運用は「利用者がブラウザで落として data/files/osaka-city/ に置く」。ページに新しいファイル名が出たら files-report に太字で合図を出す。毎日3本を取り直して、通るようになったら分かる。届出一覧.xls は平成12年からの全届出1,421件・75列で、いちばん濃い。大阪市はこのページのデータを CC-BY 4.0 で提供すると明記している。オープンデータカタログ（resource.csv 2,609件）にも届出一覧は無かった（2026-09-12確認）
- robots.txt: 許可
- HTTP 200 / utf-8 / 45,619 バイト
- **判定: Excel**
- 表 0 個 / PDFリンク 6 本 / Excel 3 本
  - PDF: 縦覧一覧(PDF形式, 232.85KB) → https://www.city.osaka.lg.jp/keizaisenryaku/page/cmsfiles/contents/0000373/373985/ju_20260818.pdf
  - PDF: 届出一覧(PDF形式, 1.28MB) → https://www.city.osaka.lg.jp/keizaisenryaku/page/cmsfiles/contents/0000373/373985/to20260630.pdf
  - PDF: 市内店舗一覧(PDF形式, 1.42MB) → https://www.city.osaka.lg.jp/keizaisenryaku/page/cmsfiles/contents/0000373/373985/si20260630.pdf
  - PDF: 手続きの流れ(PDF形式, 430.66KB) → https://www.city.osaka.lg.jp/keizaisenryaku/page/cmsfiles/contents/0000373/373985/nagare_202511.pdf
  - PDF: 経済産業省ウェブページ「大規模小売店舗を設置する者が配慮すべき事項に関する指針」（平成19年2月1日経済産業省告示第16 → http://www.meti.go.jp/policy/economy/distribution/daikibo/downloadfiles/sisin_saikaitei.pdf
  - Excel: 縦覧一覧(XLSX形式, 25.79KB) → https://www.city.osaka.lg.jp/keizaisenryaku/page/cmsfiles/contents/0000373/373985/ju_20260818.xlsx
  - Excel: 届出一覧(XLS形式, 1.51MB) → https://www.city.osaka.lg.jp/keizaisenryaku/page/cmsfiles/contents/0000373/373985/to20260630.xls
  - Excel: 市内店舗一覧(XLS形式, 505.50KB) → https://www.city.osaka.lg.jp/keizaisenryaku/page/cmsfiles/contents/0000373/373985/si20260630.xls
- 出てきた言葉: 変更 / 縦覧 / 届出 / 店舗面積
- 年度らしき表記: 平成12年 / 平成19年

### 堺市 大規模小売店舗の届出状況

- URL: https://www.city.sakai.lg.jp/sangyo/shienyuushi/kojoricchi/daikibo/todokede/index.html
- メモ: 政令市。新設・名称変更・配置変更が届出種別×年度で整理された階層インデックス。長らく空けていた穴
- robots.txt: 許可
- HTTP 200 / UTF-8 / 13,818 バイト
- **判定: わからない**
- 表 0 個 / PDFリンク 0 本 / Excel 0 本
- 出てきた言葉: 新設 / 変更 / 廃止 / 届出
- 年度らしき表記: 令和8年
- **この先を辿った: 24本** 
  -  新設の届出（法第5条第1項関係）について … **わからない**
  -  名称・代表者等の変更の届出（法第6条第1項関係）について … **わからない**
  -  施設の配置・運営方法等の変更の届出（法第6条第2項関係）について … **わからない**
  -  廃止の届出（法第6条第5項関係）について … **わからない**
  -  既存店の変更の届出（法附則第5条第1項関係）について … **わからない**
  -  承継の届出（法第11条第3項関係）について … **表** 20行×6列
  -  令和8年度 新設の届出（法第5条第1項関係）について … **表** 3行×11列 PDF2本
  -    令和7年度 新設の届出（法第5条第1項関係）について … **表** 6行×11列 PDF5本
  -    令和6年度 新設の届出（法第5条第1項関係）について … **表** 5行×11列 PDF4本
  -    令和5年度 新設の届出（法第5条第1項関係）について … **表** 2行×11列 PDF1本
  -    令和4年度 新設の届出（法第5条第1項関係）について … **表** 4行×11列 PDF3本
  -    令和8年度 名称・代表者等の変更の届出（法第6条第1項関係）について … **表** 10行×8列
  -    令和7年度 名称・代表者等の変更の届出（法第6条第1項関係）について … **表** 19行×8列
  -    令和6年度 名称・代表者等の変更の届出（法第6条第1項関係）について … **表** 16行×8列
  -    令和5年度 名称・代表者等の変更の届出（法第6条第1項関係）について … **表** 16行×8列
  -    令和7年度 施設の配置・運営方法等の変更の届出（法第6条第2項関係） … **表** 2行×12列 PDF1本
  -    令和6年度 施設の配置・運営方法等の変更の届出（法第6条第2項関係） … **わからない**
  -    令和5年度 施設の配置・運営方法等の変更の届出（法第6条第2項関係） … **表** 3行×12列 PDF2本
  -    令和4年度 施設の配置・運営方法等の変更の届出（法第6条第2項関係） … **表** 2行×12列 PDF1本
  -    令和7年度 廃止の届出（法第6条第5項関係）について … **表** 3行×5列
  -    令和6年度 廃止の届出（法第6条第5項関係）について … **わからない**
  -    令和5年度 廃止の届出（法第6条第5項関係）について … **わからない**
  -    令和4年度 廃止の届出（法第6条第5項関係）について … **表** 2行×5列
  -    既存店の変更の届出（法附則第5条第1項関係）について … **わからない**

### 高槻市 大規模小売店舗立地法に基づく大阪府への届出一覧

- URL: https://www.city.takatsuki.osaka.jp/soshiki/58/102618.html
- メモ: 題が「大規模小売店舗立地法に基づく大阪府への届出一覧」なので一覧に見えるが、中身は『大阪府へ届出がされた後、高槻市で縦覧されます』『大阪府ホームページをご確認ください』の2文だけ。店舗名も公告も意見書も0回（2026-09-11の保存ページで確認）。高槻市は移譲先ではなく大阪府が受理するので、高槻市分は大阪府のデータに入っている。取りに行かなくてよい
- **結果: 取りに行かなかった（題が「大規模小売店舗立地法に基づく大阪府への届出一覧」なので一覧に見えるが、中身は『大阪府へ届出がされた後、高槻市で縦覧されます』『大阪府ホームページをご確認ください』の2文だけ。店舗名も公告も意見書も0回（2026-09-11の保存ページで確認）。高槻市は移譲先ではなく大阪府が受理するので、高槻市分は大阪府のデータに入っている。取りに行かなくてよい）**

### 八尾市 大規模小売店舗の届出状況（全年度の入口）

- URL: https://www.city.yao.osaka.jp/sangyou_business/sangyoushinkou_kigyoushien/1012001/1012008/index.html
- メモ: 年度別ページを束ねるインデックス。単年度ページは年度が変わると古くなるのでこちらを見る
- robots.txt: 許可
- HTTP 200 / UTF-8 / 35,236 バイト
- **判定: わからない**
- 表 0 個 / PDFリンク 0 本 / Excel 0 本
- 出てきた言葉: 変更 / 届出
- 年度らしき表記: 令和5年 / 令和6年 / 令和7年 / 令和8年
- **この先を辿った: 9本** 
  -  令和8年度の大規模小売店舗の届出状況 … **PDF** PDF3本
  -  令和7年度の大規模小売店舗の届出状況 … **PDF** PDF4本
  -  令和6年度の大規模小売店舗の届出状況 … **PDF** PDF5本
  -  令和5年度の大規模小売店舗の届出状況 … **表** 5行×8列
  -  大規模小売店舗立地法第6条第1項に基づく届出の概要（店舗名称：マナベ … **わからない**
  -  大規模小売店舗立地法第6条第1項に基づく届出の概要（店舗名称：ダイレ … **わからない**
  -  大規模小売店舗立地法第5条第1項に基づく届出の概要（店舗名称：(仮称 … **わからない**
  -  大規模小売店舗立地法第5条第1項に基づく届出の概要（店舗名称：（仮称 … **わからない**
  -  大規模小売店舗立地法第5条第1項に基づく届出の概要（店舗名称：（仮称 … **わからない**

### 吹田市 大規模小売店舗の出店に関する届出

- URL: https://www.city.suita.osaka.jp/sangyo/1018028/1018041/1011521.html
- メモ: 一覧を持っていなかった。大阪府のページへ外部リンクしているだけ（2026-09-11の保存ページで確認）。中規模小売店舗の届出は別にある
- **結果: 取りに行かなかった（一覧を持っていなかった。大阪府のページへ外部リンクしているだけ（2026-09-11の保存ページで確認）。中規模小売店舗の届出は別にある）**

### （参考）東京都 届出状況一覧 平成12年度〜

- URL: https://www.sangyo-rodo.metro.tokyo.lg.jp/chushou/shoko/chiiki/daikibo
- メモ: 前のURLは一覧ページではなかった。親ページに変更。年度別の一覧はこの下にぶら下がっている
- robots.txt: 許可
- HTTP 200 / UTF-8 / 553,190 バイト
- **判定: わからない**
- 表 0 個 / PDFリンク 0 本 / Excel 0 本
- 出てきた言葉: 縦覧 / 届出
- 年度らしき表記: 令和５年 / 令和８年 / 平成12年
- **この先を辿った: 10本** 
  -  ４．公告・縦覧の状況 … **わからない**
  -  8．届出状況一覧（平成12年度～） … **わからない**
  -    届出状況（新設） … **わからない**
  -    届出状況（変更） … **わからない**
  -    届出状況（廃止） … **わからない**
  -    届出状況（承継） … **わからない**
  -    平成27年度届出状況一覧 （341.5KB） … **わからない**
  -    平成26年度届出状況一覧 （317.9KB） … **わからない**
  -    平成25年度届出状況一覧 （405.4KB） … **わからない**
  -    平成24年度届出状況一覧 （383.9KB） … **わからない**

### 豊中市 届出状況

- URL: https://www.city.toyonaka.osaka.jp/machi/sangyoushinkou/kigyoricchi/daikibokouritenpo/todokede.html
- メモ: 制度解説のindexとは別の「届出状況」専用ページ
- robots.txt: 許可
- HTTP 200 / UTF-8 / 86,034 バイト
- **判定: 表**
- 表 5 個 / PDFリンク 24 本 / Excel 0 本
- いちばん大きい表: 66 行 × 7 列
  - 見出しらしき行: 店舗の名称 | 店舗の所在地 | 届出日 | 縦覧期間 | 変更理由 | 変更事項 | 住民等の意見の概要
  - PDF: 届出概要(PDF:100KB) → https://www.city.toyonaka.osaka.jp/machi/sangyoushinkou/kigyoricchi/daikibokouritenpo/todokede.files/0612okhozumi.pdf
  - PDF: 届出概要(PDF:110KB) → https://www.city.toyonaka.osaka.jp/machi/sangyoushinkou/kigyoricchi/daikibokouritenpo/todokede.files/20240606yunikuro.pdf
  - PDF: 届出概要(PDF:121KB) → https://www.city.toyonaka.osaka.jp/machi/sangyoushinkou/kigyoricchi/daikibokouritenpo/todokede.files/0415iontown.pdf
  - PDF: 届出概要(PDF:119KB) → https://www.city.toyonaka.osaka.jp/machi/sangyoushinkou/kigyoricchi/daikibokouritenpo/todokede.files/1016sennri.pdf
  - PDF: 届出概要(PDF:121KB) → https://www.city.toyonaka.osaka.jp/machi/sangyoushinkou/kigyoricchi/daikibokouritenpo/todokede.files/s15jyoushin0319.pdf
- 出てきた言葉: 新設 / 変更 / 廃止 / 縦覧 / 届出
- 年度らしき表記: 令和2年 / 令和3年 / 令和4年 / 令和5年 / 令和6年 / 令和7年 / 令和8年 / 令和9年

### 箕面市 箕面市の届出状況

- URL: https://www.city.minoh.lg.jp/syoukou/daikibominoh.html
- メモ: 2市2町（箕面・池田・豊能・能勢）の共同処理で箕面市が幹事。これは箕面市分の届出状況
- robots.txt: 許可
- HTTP 200 / utf-8 / 30,612 バイト
- **判定: 表**
- 表 6 個 / PDFリンク 1 本 / Excel 0 本
- いちばん大きい表: 6 行 × 6 列
  - 見出しらしき行: 店舗の名称 | 店舗の所在地 | 届出日 | 縦覧期限 | 変更事項 | 住民等の意見の概要
  - PDF: 届出概要（PDF：45KB） → https://www.city.minoh.lg.jp/syoukou/documents/suvland_5-1.pdf
- 出てきた言葉: 新設 / 変更 / 縦覧 / 届出 / 店舗面積
- 年度らしき表記: 令和5年 / 令和6年 / 令和7年 / 令和8年

### 枚方市 届出状況

- URL: https://www.city.hirakata.osaka.jp/0000003373.html
- メモ: アルプラザ枚方・枚方T-SITE・フォレオひらかた等の個別届出が並ぶ。告示PDFも同じ配下
- robots.txt: 許可
- HTTP 200 / UTF-8 / 88,940 バイト
- **判定: 表**
- 表 6 個 / PDFリンク 45 本 / Excel 0 本
- いちばん大きい表: 65 行 × 6 列
  - 見出しらしき行: 店舗名称 | 所在地 | 設置者 | 届出日 | 変更事項 | 住民等の意見の概要
  - PDF: 意見概要 （仮称）KUZUHA MALL 南館 (PDF形式、106.78KB) → https://www.city.hirakata.osaka.jp/cmsfiles/contents/0000003/3373/36543.pdf
  - PDF: 届出概要 （仮称）枚方市大峰南町物販店舗 (PDF形式、106.76KB) → https://www.city.hirakata.osaka.jp/cmsfiles/contents/0000003/3373/34151.pdf
  - PDF: 届出概要 （仮称）ドラッグユタカ枚方西招提店 (PDF形式、112.28KB) → https://www.city.hirakata.osaka.jp/cmsfiles/contents/0000003/3373/45787.pdf
  - PDF: 届出概要 （仮称）ニトリモール枚方 (PDF形式、127.17KB) → https://www.city.hirakata.osaka.jp/cmsfiles/contents/0000003/3373/65207.pdf
  - PDF: 意見概要 （仮称）ニトリモール枚方 (PDF形式、109.90KB) → https://www.city.hirakata.osaka.jp/cmsfiles/contents/0000003/3373/72084.pdf
- 出てきた言葉: 新設 / 変更 / 廃止 / 縦覧 / 届出
- 年度らしき表記: 令和2年 / 令和3年 / 令和4年 / 令和5年 / 令和6年 / 令和7年 / 令和8年 / 平成24年

### 茨木市 届出状況

- URL: https://www.city.ibaraki.osaka.jp/kikou/sangyo/shoukou/menu/daikibotyukibokouritenpo/tensyutsu/48906.html
- メモ: 届出年月日と縦覧期間つきで案件が載る。サイト改編でパスが移行中の可能性ありとの指摘あり
- robots.txt: 許可
- HTTP 200 / utf-8 / 70,044 バイト
- **判定: 表**
- 表 6 個 / PDFリンク 0 本 / Excel 0 本
- いちばん大きい表: 58 行 × 3 列
  - 見出しらしき行: 名称 | 所在地 | 届出日
- 出てきた言葉: 新設 / 変更 / 廃止 / 届出 / 店舗面積
- 年度らしき表記: 令和2年 / 令和3年 / 令和4年 / 令和5年 / 令和6年 / 令和7年 / 令和8年 / 平成12年

### 和泉市 届出状況

- URL: https://www.city.osaka-izumi.lg.jp/bizisan/shoukou/rixcchihou/todokedejoukyou/index.html
- メモ: 12年分すべてPDF。「届出の概要・縦覧期間等」が58本ある。大阪でいちばん本数が多い
- robots.txt: 許可
- HTTP 200 / utf-8 / 39,218 バイト
- **判定: わからない**
- 表 0 個 / PDFリンク 0 本 / Excel 0 本
- 出てきた言葉: 変更 / 届出
- 年度らしき表記: 令和2年 / 令和3年 / 令和4年 / 令和5年 / 令和6年 / 令和7年 / 令和8年 / 平成25年
- **この先を辿った: 12本** 
  -  平成28年度の大規模小売店舗立地法の届出状況 … **PDF** PDF3本
  -  平成25年度の大規模小売店舗立地法の届出状況 … **PDF** PDF6本
  -  平成29年度の大規模小売店舗立地法の届出状況 … **PDF** PDF6本
  -  平成30年度の大規模小売店舗立地法の届出状況 … **PDF** PDF8本
  -  平成31年度の大規模小売店舗立地法の届出状況 … **PDF** PDF6本
  -  令和2年度の大規模小売店舗立地法の届出状況 … **PDF** PDF3本
  -  令和3年度の大規模小売店舗立地法の届出状況 … **PDF** PDF4本
  -  令和4年度の大規模小売店舗立地法の届出状況 … **PDF** PDF6本
  -  令和5年度の大規模小売店舗立地法の届出状況 … **PDF** PDF6本
  -  令和6年度の大規模小売店舗立地法の届出状況 … **PDF** PDF4本
  -  令和7年度の大規模小売店舗立地法の届出状況 … **PDF** PDF5本
  -  令和8年度の大規模小売店舗立地法の届出状況 … **PDF** PDF4本

### 岸和田市 大店届出

- URL: https://www.city.kishiwada.lg.jp/page/43-daitentodokede.html
- メモ: 利用者が実際に開いて確認したURL。前は検索から拾った www.city.kishiwada.osaka.jp/soshiki/43/... を入れていたが、ドメインもパスも違ってDNSが引けなかった。43 と daitentodokede の部分だけ合っていた
- robots.txt: 許可
- HTTP 200 / utf-8 / 43,017 バイト
- **判定: 表**
- 表 3 個 / PDFリンク 21 本 / Excel 0 本
- いちばん大きい表: 4 行 × 10 列
  - 見出しらしき行: 届出の名称 | 店舗の所在地 | 設置する者 | 届出日 | 縦覧期間 | 説明会会場 | 説明会日時 | 住民意見 | 市意見 | 市留意事項
  - PDF: ジョーシン岸和田店　6条1項届出　告示文 [PDFファイル／37KB] → https://www.city.kishiwada.lg.jp/uploaded/attachment/164922.pdf
  - PDF: ジョーシン岸和田店　縦覧資料　6条1項　届出書 [PDFファイル／39KB] → https://www.city.kishiwada.lg.jp/uploaded/attachment/164925.pdf
  - PDF: ゲオ岸和田店　6条1項届出　告示文 [PDFファイル／35KB] → https://www.city.kishiwada.lg.jp/uploaded/attachment/164924.pdf
  - PDF: ゲオ岸和田店　縦覧資料　6条1項　届出書 [PDFファイル／34KB] → https://www.city.kishiwada.lg.jp/uploaded/attachment/164926.pdf
  - PDF: アクロスプラザ東岸和田　6条1項届出　告示文 [PDFファイル／59KB] → https://www.city.kishiwada.lg.jp/uploaded/attachment/165580.pdf
- 出てきた言葉: 新設 / 変更 / 廃止 / 縦覧 / 届出 / 店舗面積
- 年度らしき表記: 令和6年 / 令和7年 / 令和8年 / 令和9年

### 貝塚市 大店立地法届出状況

- URL: https://www.city.kaizuka.lg.jp/kakuka/sogoseisaku/sangyo/menu/daitenrittihounituite/daitenrittihoutodokedejoukyou.html
- メモ: 表もPDFも0だが、箇条書きが62個ある。リストの形で出している可能性。辿る先も0本なので、別の読み方が要る
- robots.txt: 許可
- HTTP 200 / utf-8 / 51,305 バイト
- **判定: わからない**
- 表 0 個 / PDFリンク 0 本 / Excel 0 本
- 出てきた言葉: 新設 / 変更 / 縦覧 / 届出 / 店舗面積
- 年度らしき表記: 令和2年 / 令和3年 / 令和4年 / 令和5年 / 令和6年 / 令和7年 / 平成25年 / 平成26年

### 松原市 届出受理等について

- URL: https://www.city.matsubara.lg.jp/docs/page3041.html
- メモ: コーナン松原市役所前店・イオンタウン松原などの「届出の概要」PDFが配下にある
- robots.txt: 許可
- HTTP 200 / UTF-8 / 72,751 バイト
- **判定: 表**
- 表 1 個 / PDFリンク 37 本 / Excel 0 本
- いちばん大きい表: 31 行 × 5 列
  - 見出しらしき行: 区分 | 店舗名称・住所 | 届出日 | 届出書の概要 | 縦覧期間
			（意見提出期間）
  - PDF: 意見書様式 (PDFファイル: 41.0KB) → https://www.city.matsubara.lg.jp/fs/1/9/3/0/3/6/_/20130108-120738.pdf
  - PDF: 届出書概要[50KB pdfファイル] → https://www.city.matsubara.lg.jp/fs/1/9/3/0/3/7/_/20130108-121756.pdf
  - PDF: 届出書概要[42KB pdfファイル] → https://www.city.matsubara.lg.jp/fs/1/9/3/0/3/8/_/20140225-180711.pdf
  - PDF: 別表[74KB pdfファイル] → https://www.city.matsubara.lg.jp/fs/1/9/3/0/3/9/_/20140225-180759.pdf
  - PDF: 届出書概要[83KB pdfファイル] → https://www.city.matsubara.lg.jp/fs/1/9/3/0/4/0/_/20150203-085657.pdf
- 出てきた言葉: 新設 / 変更 / 縦覧 / 届出 / 店舗面積
- 年度らしき表記: 令和2年 / 令和3年 / 令和4年 / 令和5年 / 令和6年 / 令和7年 / 令和8年 / 平成23年

### 泉南市 届出

- URL: https://www.city.sennan.lg.jp/kakuka/shiminseikatu/sangyoushinkou/shokorodokakari/town/daikibo/todokede/12417.html
- メモ: 移譲市町村。届出状況の一覧ページと判定
- robots.txt: 許可
- HTTP 200 / utf-8 / 44,378 バイト
- **判定: 表**
- 表 2 個 / PDFリンク 0 本 / Excel 0 本
- いちばん大きい表: 3 行 × 8 列
  - 見出しらしき行: 店舗名称 | 店舗所在地 | 届出日 | 届出の縦覧期間 | 説明会開催日時・場所 | 市民等の意見提出期限 | 市の意見 | 意見の縦覧期間
- 出てきた言葉: 新設 / 変更 / 廃止 / 縦覧 / 届出 / 店舗面積
- 年度らしき表記: 令和8年 / 平成12年

### 阪南市 大規模小売店舗立地法の届出

- URL: https://www.city.hannan.lg.jp/kakuka/mirai/kikaku/daikibokouritennporittihou/index.html
- メモ: 移譲市町村。届出状況の一覧ページと判定
- robots.txt: 許可
- HTTP 200 / utf-8 / 41,290 バイト
- **判定: わからない**
- 表 0 個 / PDFリンク 0 本 / Excel 0 本
- 出てきた言葉: 新設 / 変更 / 届出 / 店舗面積 / 開店
- 年度らしき表記: 令和2年 / 令和3年 / 令和4年 / 令和5年 / 令和6年 / 令和7年 / 平成23年 / 平成24年
- **この先を辿った: 12本** （15本見つかったが上限12本まで）
  -  令和7年度届出状況 … **表** 7行×2列
  -  令和6年度届出状況 … **表** 7行×2列
  -  令和5年度届出状況 … **表** 7行×2列 PDF2本
  -  令和4年度届出状況 … **表** 7行×2列
  -  令和3年度届出状況 … **表** 7行×2列 PDF2本
  -  令和2年度届出状況 … **表** 7行×2列 PDF1本
  -  平成31年度届出状況 … **表** 7行×2列
  -  平成30年度届出状況 … **表** 7行×2列
  -  平成29年度届出状況 … **表** 7行×2列
  -  平成28年度届出状況 … **表** 7行×2列 PDF2本
  -  平成27年度届出状況 … **表** 7行×2列
  -  平成26年度届出状況 … **表** 7行×2列

### 箕面市 2市2町の窓口（池田市・豊能町・能勢町ぶん）

- URL: https://www.city.minoh.lg.jp/syoukou/daikibo.html
- メモ: 池田市・豊能町・能勢町はここが窓口。案内ページだが届出件数の記載がある。3自治体で同じURLなので1本にまとめた
- robots.txt: 許可
- HTTP 200 / utf-8 / 30,294 バイト
- **判定: わからない**
- 表 0 個 / PDFリンク 1 本 / Excel 0 本
  - PDF: 大規模小売店舗の出店等に関する手続き・届出書類等の手引き（PDF：172KB） → https://www.city.minoh.lg.jp/syoukou/documents/r8_minoh_daitentebiki.pdf
- 出てきた言葉: 新設 / 変更 / 廃止 / 縦覧 / 届出 / 店舗面積
- **この先を辿った: 3本** 
  -  箕面市の届出状況（別ウィンドウが開きます） … **表** 6行×6列 PDF1本
  -  能勢町の届出状況（別ウィンドウが開きます） … **表** 2行×7列 PDF1本
  -  中規模小売店舗の届出について … **わからない**

### 門真市 大規模小売店舗立地法

- URL: https://www.city.kadoma.osaka.jp/soshiki/shiminbunkabu/6/3/4/2484.html
- メモ: 案内ページと見られる。平成28年度以前は大阪府側にあるとの案内あり。実地で確かめる
- robots.txt: 許可
- HTTP 200 / utf-8 / 75,431 バイト
- **判定: 表**
- 表 7 個 / PDFリンク 30 本 / Excel 0 本
- いちばん大きい表: 18 行 × 5 列
  - 見出しらしき行: 店舗の名称 | 店舗の所在地 | 届出日 | 届出概要、縦覧期間など | 市町村、住民等の意見の概要
  - PDF: 大規模小売店舗立地法解説リーフレット (PDFファイル: 121.1KB) → https://www.city.kadoma.osaka.jp/material/files/group/14/daiten_01.pdf
  - PDF: 大規模小売店舗立地法の基本的な手続きの流れ (PDFファイル: 35.6KB) → https://www.city.kadoma.osaka.jp/material/files/group/14/daiten_02.pdf
  - PDF: 大規模小売店舗立地法の手続きが必要な場合 (PDFファイル: 76.5KB) → https://www.city.kadoma.osaka.jp/material/files/group/14/daikibo_03.pdf
  - PDF: 大規模小売店舗の出店等に関する手続き・届出書類等の手引き (PDFファイル: 152.0KB) → https://www.city.kadoma.osaka.jp/material/files/group/14/daiten_03.pdf
  - PDF: 門真市大規模小売店舗立地法運用事務手続要綱 (PDFファイル: 259.5KB) → https://www.city.kadoma.osaka.jp/material/files/group/14/daikibo_05.pdf
- 出てきた言葉: 新設 / 変更 / 廃止 / 縦覧 / 届出 / 店舗面積 / 開店
- 年度らしき表記: 平成19年

### 大阪狭山市 大規模小売店舗立地法

- URL: https://www.city.osakasayama.osaka.jp/sosiki/siminseikatsubu/sangyounigiwaizukuri/4/1/1410228705740.html
- メモ: PDFが4本あるが、実地で見たら「手引き」「要綱」「しおり」「フロー図」だけで届出の一覧ではなかった（2026-09-11）。一覧を出していない自治体
- robots.txt: 許可
- HTTP 200 / utf-8 / 168,967 バイト
- **判定: PDF**
- 表 0 個 / PDFリンク 4 本 / Excel 0 本
  - PDF: 大規模小売店舗立地法「しおり」 (PDFファイル: 177.4KB) → https://www.city.osakasayama.osaka.jp/material/files/group/31/daitenshiori.pdf
  - PDF: 出店の手引き (PDFファイル: 300.6KB) → https://www.city.osakasayama.osaka.jp/material/files/group/31/daitentebiki.pdf
  - PDF: 大阪狭山市大規模小売店舗運用事務手続要綱 (PDFファイル: 142.6KB) → https://www.city.osakasayama.osaka.jp/material/files/group/31/daitenyoukou.pdf
  - PDF: 大規模小売店舗の出店（変更）に関する様式集 (PDFファイル: 636.7KB) → https://www.city.osakasayama.osaka.jp/material/files/group/31/daitenyoushiki.pdf
- 出てきた言葉: 新設 / 変更 / 縦覧 / 届出 / 店舗面積 / 開店
- 年度らしき表記: 平成24年

### 熊取町 大規模小売店舗立地法

- URL: https://www.town.kumatori.lg.jp/soshiki/sangyo_shinko/gyomu/sangyo_shinko/shokogyo/2357.html
- メモ: 案内ページと見られる。実地で確かめる
- robots.txt: 許可
- HTTP 200 / utf-8 / 69,185 バイト
- **判定: 表**
- 表 1 個 / PDFリンク 2 本 / Excel 0 本
- いちばん大きい表: 3 行 × 6 列
  - 見出しらしき行: 届出書類名 | 店舗の名称及び所在地 | 届出日 | 届出書の提出理由 | 縦覧期間 | 提出期限
  - PDF: 大規模小売店舗立地法の出店等に関する手続き (PDFファイル: 319.0KB) → https://www.town.kumatori.lg.jp/material/files/group/14/tebikinew.pdf
  - PDF: 大規模小売店舗立地法手続要綱 (PDFファイル: 83.9KB) → https://www.town.kumatori.lg.jp/material/files/group/14/tetudukiyoukou.pdf
- 出てきた言葉: 新設 / 変更 / 廃止 / 縦覧 / 届出 / 店舗面積 / 開店
- 年度らしき表記: 令和4年 / 平成19年 / 平成25年 / 平成27年

### 泉佐野市 届出

- URL: https://www.city.izumisano.lg.jp/kakuka/seikatsu/shoko/menu/jigyosyo/todokede/1613433836928.html
- メモ: PDFが4本あるが、実地で見たら「手引き」「要綱」「しおり」「フロー図」だけで届出の一覧ではなかった（2026-09-11）。一覧を出していない自治体
- robots.txt: 許可
- HTTP 200 / utf-8 / 61,437 バイト
- **判定: PDF**
- 表 0 個 / PDFリンク 4 本 / Excel 0 本
  - PDF: 事務の流れ（フロー図） (PDFファイル: 81.9KB) → https://www.city.izumisano.lg.jp/material/files/group/23/furo20180401.pdf
  - PDF: 泉佐野市大規模小売店舗立地法手続要綱 (PDFファイル: 163.0KB) → https://www.city.izumisano.lg.jp/material/files/group/23/daitenyoukou.pdf
  - PDF: 大規模小売店舗の出店等に関する手続き・届出書類等の手引き (PDFファイル: 337.6KB) → https://www.city.izumisano.lg.jp/material/files/group/23/daitentebiki.pdf
  - PDF: 手引き（別表） (PDFファイル: 78.8KB) → https://www.city.izumisano.lg.jp/material/files/group/23/daitentebikibeppyou.pdf
- 出てきた言葉: 新設 / 変更 / 廃止 / 縦覧 / 届出 / 店舗面積 / 開店
- 年度らしき表記: 平成30年

### 河内長野市 大規模小売店舗立地法のお知らせ

- URL: https://www.city.kawachinagano.lg.jp/soshiki/16/100545.html
- メモ: 「縦覧リスト」PDFが一覧そのもの。設置者と店舗面積まで入っている
- robots.txt: 許可
- HTTP 200 / utf-8 / 17,313 バイト
- **判定: わからない**
- 表 0 個 / PDFリンク 2 本 / Excel 0 本
  - PDF: 縦覧リスト [PDFファイル／62KB] → https://www.city.kawachinagano.lg.jp/uploaded/attachment/48096.pdf
  - PDF: 意見書（PDF） [PDFファイル／88KB] → https://www.city.kawachinagano.lg.jp/uploaded/attachment/39098.pdf
- 出てきた言葉: 新設 / 変更 / 縦覧 / 届出

### 堺市 中規模小売店舗の届出状況

- URL: https://www.city.sakai.lg.jp/sangyo/shienyuushi/kojoricchi/chukouritenpo/chukiboichiran.html
- メモ: 中規模で一覧を公開している数少ない例。大店立地法が拾えない1000平米以下を拾える
- robots.txt: 許可
- HTTP 200 / UTF-8 / 14,002 バイト
- **判定: わからない**
- 表 0 個 / PDFリンク 0 本 / Excel 0 本
- 出てきた言葉: 届出
- 年度らしき表記: 令和3年 / 令和4年 / 令和5年 / 令和6年 / 令和7年 / 令和8年
- **この先を辿った: 6本** 
  -  中規模小売店舗の届出状況（令和8年度） … **表** 3行×9列
  -  中規模小売店舗の届出状況（令和7年度） … **表** 8行×9列
  -  中規模小売店舗の届出状況（令和6年度） … **表** 6行×9列
  -  中規模小売店舗の届出状況（令和5年度） … **表** 4行×9列
  -  中規模小売店舗の届出状況（令和4年度） … **表** 17行×9列
  -  中規模小売店舗の届出状況（令和3年度） … **表** 8行×9列

### 八尾市 中規模小売店舗

- URL: https://www.city.yao.osaka.jp/sangyou_business/sangyoushinkou_kigyoushien/1012001/1012003.html
- メモ: 同上。一覧の可能性ありとの判定。実地で確かめる
- robots.txt: 許可
- HTTP 200 / UTF-8 / 52,137 バイト
- **判定: 表**
- 表 1 個 / PDFリンク 0 本 / Excel 0 本
- いちばん大きい表: 98 行 × 5 列
  - 見出しらしき行: 年度 | 届出日 | 店舗名称 | 所在地（地番） | 店舗面積
- 出てきた言葉: 変更 / 届出 / 店舗面積
- 年度らしき表記: 令和2年 / 令和3年 / 令和4年 / 令和5年 / 令和6年 / 令和8年 / 平成12年 / 平成13年

### 岬町 大規模小売店舗立地法

- URL: 
- メモ: 移譲先だが、大店立地法の届出ページが検索で見つからなかった（2026-09-11調査）。届出実績が無い可能性
- **結果: 取りに行かなかった（移譲先だが、大店立地法の届出ページが検索で見つからなかった（2026-09-11調査）。届出実績が無い可能性）**

### （参考）大阪市オープンデータポータル 添付ファイル一覧

- URL: https://data.city.osaka.lg.jp/
- メモ: 大阪市の添付ファイルのメタデータを日次CSVで出しているらしいが、/odcsv/ もトップページも GitHub Actions から40秒以内に応答が無かった（2026-09-12、2回）。国外からは見えない可能性が高い。止めた
- **結果: 取りに行かなかった（大阪市の添付ファイルのメタデータを日次CSVで出しているらしいが、/odcsv/ もトップページも GitHub Actions から40秒以内に応答が無かった（2026-09-12、2回）。国外からは見えない可能性が高い。止めた）**

### （参考）大阪府 著作権・リンクについて

- URL: https://www.pref.osaka.lg.jp/o070050/koho/information/use.html
- メモ: 届出ページの下部から辿った利用規約ページ。出典表記の書き方を読むために保存する（2026-09-12追加）
- robots.txt: 許可
- HTTP 200 / utf-8 / 18,154 バイト
- **判定: わからない**
- 表 0 個 / PDFリンク 0 本 / Excel 0 本
- 出てきた言葉: 変更

### （参考）兵庫県 リンク・著作権・免責事項

- URL: https://web.pref.hyogo.lg.jp/about_link.html
- メモ: 届出ページの下部から辿った利用規約ページ。出典表記の書き方を読むために保存する（2026-09-12追加）
- robots.txt: 許可
- HTTP 200 / utf-8 / 17,678 バイト
- **判定: わからない**
- 表 1 個 / PDFリンク 0 本 / Excel 0 本
- いちばん大きい表: 2 行 × 2 列
  - 見出しらしき行: 【HTMLの記述方法】
			<a href="
- 出てきた言葉: 変更

### （参考）堺市 リンク・著作権・免責事項

- URL: https://www.city.sakai.lg.jp/aboutweb/linkchosakuken.html
- メモ: 届出ページの下部から辿った利用規約ページ。出典表記の書き方を読むために保存する（2026-09-12追加）
- robots.txt: 許可
- HTTP 200 / UTF-8 / 14,355 バイト
- **判定: わからない**
- 表 0 個 / PDFリンク 0 本 / Excel 0 本
- 出てきた言葉: 変更

### （参考）神戸市 ホームページのご利用案内

- URL: https://www.city.kobe.lg.jp/homepage/index.html
- メモ: 届出ページの下部から辿った「ホームページのご利用案内」。中身は目次で、利用規約は /a57337/homepage/rule.html にある（2026-09-12に読んだ）
- robots.txt: 許可
- HTTP 200 / UTF-8 / 12,807 バイト
- **判定: わからない**
- 表 0 個 / PDFリンク 0 本 / Excel 0 本

### （参考）大阪市オープンデータポータル（www側の入口）

- URL: https://www.city.osaka.lg.jp/contents/wdu290/opendata/
- メモ: 大阪市オープンデータの入口（www側）。開けて、全データのURL一覧 resource.csv（2,609件）を落とした（2026-09-12）。大店立地法で引っかかるのは「環境面の協議件数」の統計4件だけで、届出一覧はオープンデータには無かった。止めた
- **結果: 取りに行かなかった（大阪市オープンデータの入口（www側）。開けて、全データのURL一覧 resource.csv（2,609件）を落とした（2026-09-12）。大店立地法で引っかかるのは「環境面の協議件数」の統計4件だけで、届出一覧はオープンデータには無かった。止めた）**

### （参考）神戸市 利用規約・リンク・免責事項など

- URL: https://www.city.kobe.lg.jp/a57337/homepage/rule.html
- メモ: 神戸市の利用規約本体（2026-09-12に読んだ）。PDF「神戸市ウェブサイト利用規約」は政府標準利用規約 第2.0版準拠・CC BY 4.0互換で、サイト全体のコンテンツを出典明記で複製・加工・商用利用できる。規約が変わったら分かるよう毎日保存を続ける
- robots.txt: 許可
- HTTP 200 / UTF-8 / 17,155 バイト
- **判定: わからない**
- 表 0 個 / PDFリンク 1 本 / Excel 0 本
  - PDF: 神戸市ウェブサイト利用規約（PDF：124KB） → https://www.city.kobe.lg.jp/documents/19135/20170630041802-1.pdf
- 出てきた言葉: 変更

### （参考）兵庫県 オープンデータ

- URL: https://web.pref.hyogo.lg.jp/pref/cate3_661.html
- メモ: 兵庫県の著作権ページから辿ったオープンデータの入口。大店立地法の縦覧状況がオープンデータに含まれるか、利用規約（政府標準利用規約か）を見る（2026-09-12追加）
- robots.txt: 許可
- HTTP 200 / utf-8 / 14,907 バイト
- **判定: わからない**
- 表 0 個 / PDFリンク 0 本 / Excel 0 本
- 出てきた言葉: 変更

### （参考）兵庫県 関連サイトに掲載のオープンデータ（デジタル戦略課）

- URL: https://web.pref.hyogo.lg.jp/kk26/johoseisaku/opendata.html
- メモ: 兵庫県オープンデータの本体（2026-09-12に読んだ）。カタログ専用の利用規約PDF kiyaku_opendata.pdf を落として読んだ：カタログ掲載の著作物は注があるものを除き CC BY 4.0。加工時は「この○○は、以下の著作物を改変して利用しています。[タイトル]、[兵庫県]」と書く。県HPにも同じデータがある場合はカタログ規約が優先（第2条1項）。pdf:true を付けたら同じページのExcel/CSV 116本まで落としてしまったので外した（files.py 側でも参考ソースはExcel/CSVを取らないようにした）
- robots.txt: 許可
- HTTP 200 / utf-8 / 68,432 バイト
- **判定: 表**
- 表 1 個 / PDFリンク 2 本 / Excel 116 本
- いちばん大きい表: 4 行 × 6 列
  - 見出しらしき行: 神戸 | 神戸市（外部サイトへリンク） | 北播磨 | 西脇市（外部サイトへリンク）
			三木市（外部 | 但馬 | 豊岡市（外部サイトへリンク）
			養父市（外部
  - PDF: オープンデータカタログページ利用規約（PDF：115KB） → https://web.pref.hyogo.lg.jp/kk26/johoseisaku/documents/kiyaku_opendata.pdf
  - PDF: 犯罪発生状況のウェブサイトに掲載する統一的注記（PDF：67KB）（別ウィンドウで開きます） → https://web.pref.hyogo.lg.jp/kk26/johoseisaku/documents/noter7renew.pdf
  - Excel: 令和7年中の犯罪発生状況（窃盗・自転車盗）（CSV：943KB）（別ウィンドウで開きます） → https://web.pref.hyogo.lg.jp/kk26/johoseisaku/documents/hyogo_2025zitensyatou.csv
  - Excel: 令和7年中の犯罪発生状況（窃盗・オートバイ盗）（CSV：74KB）（別ウィンドウで開きます） → https://web.pref.hyogo.lg.jp/kk26/johoseisaku/documents/hyogo_2025ootobaitou.csv
  - Excel: 令和7年中の犯罪発生状況（窃盗・自動車盗）（CSV：15KB）（別ウィンドウで開きます） → https://web.pref.hyogo.lg.jp/kk26/johoseisaku/documents/hyogo_2025zidousyatou.csv
  - Excel: 令和7年中の犯罪発生状況（窃盗・自動販売機ねらい）（CSV：11KB）（別ウィンドウで開きます） → https://web.pref.hyogo.lg.jp/kk26/johoseisaku/documents/hyogo_2025zidouhanbaikinerai.csv
  - Excel: 令和7年中の犯罪発生状況（窃盗・部品ねらい）（CSV：64KB）（別ウィンドウで開きます） → https://web.pref.hyogo.lg.jp/kk26/johoseisaku/documents/hyogo_2025buhinnerai.csv
- 出てきた言葉: 変更
- 年度らしき表記: 令和2年 / 令和3年 / 令和4年 / 令和5年 / 令和6年 / 令和7年 / 令和8年 / 平成12年

### （参考）兵庫県 オープンデータカタログ

- URL: https://web.pref.hyogo.lg.jp/opendata/index.php
- メモ: 兵庫県オープンデータカタログの入口。2026-09-12に全924件を100件ずつ10ページで見たが、大店立地法の縦覧状況・届出は登録されていなかった（小売関係は商業統計・経済センサスのみ）。キーワード「大規模小売」も0件。カタログ規約（CC BY 4.0）は縦覧状況には及ばない。止めた
- **結果: 取りに行かなかった（兵庫県オープンデータカタログの入口。2026-09-12に全924件を100件ずつ10ページで見たが、大店立地法の縦覧状況・届出は登録されていなかった（小売関係は商業統計・経済センサスのみ）。キーワード「大規模小売」も0件。カタログ規約（CC BY 4.0）は縦覧状況には及ばない。止めた）**

### （参考）兵庫県 オープンデータカタログ 一覧 1/10

- URL: https://web.pref.hyogo.lg.jp/opendata/index.php?p=1_1&asc=data_link_title&displayedresults=100
- メモ: 2026-09-12に一度見た。924件の一覧に大店立地法の縦覧状況・届出は無く、キーワード「大規模小売」も0件だった。止めた
- **結果: 取りに行かなかった（2026-09-12に一度見た。924件の一覧に大店立地法の縦覧状況・届出は無く、キーワード「大規模小売」も0件だった。止めた）**

### （参考）兵庫県 オープンデータカタログ 一覧 2/10

- URL: https://web.pref.hyogo.lg.jp/opendata/index.php?p=2_1&asc=data_link_title&displayedresults=100
- メモ: 2026-09-12に一度見た。924件の一覧に大店立地法の縦覧状況・届出は無く、キーワード「大規模小売」も0件だった。止めた
- **結果: 取りに行かなかった（2026-09-12に一度見た。924件の一覧に大店立地法の縦覧状況・届出は無く、キーワード「大規模小売」も0件だった。止めた）**

### （参考）兵庫県 オープンデータカタログ 一覧 3/10

- URL: https://web.pref.hyogo.lg.jp/opendata/index.php?p=3_1&asc=data_link_title&displayedresults=100
- メモ: 2026-09-12に一度見た。924件の一覧に大店立地法の縦覧状況・届出は無く、キーワード「大規模小売」も0件だった。止めた
- **結果: 取りに行かなかった（2026-09-12に一度見た。924件の一覧に大店立地法の縦覧状況・届出は無く、キーワード「大規模小売」も0件だった。止めた）**

### （参考）兵庫県 オープンデータカタログ 一覧 4/10

- URL: https://web.pref.hyogo.lg.jp/opendata/index.php?p=4_1&asc=data_link_title&displayedresults=100
- メモ: 2026-09-12に一度見た。924件の一覧に大店立地法の縦覧状況・届出は無く、キーワード「大規模小売」も0件だった。止めた
- **結果: 取りに行かなかった（2026-09-12に一度見た。924件の一覧に大店立地法の縦覧状況・届出は無く、キーワード「大規模小売」も0件だった。止めた）**

### （参考）兵庫県 オープンデータカタログ 一覧 5/10

- URL: https://web.pref.hyogo.lg.jp/opendata/index.php?p=5_1&asc=data_link_title&displayedresults=100
- メモ: 2026-09-12に一度見た。924件の一覧に大店立地法の縦覧状況・届出は無く、キーワード「大規模小売」も0件だった。止めた
- **結果: 取りに行かなかった（2026-09-12に一度見た。924件の一覧に大店立地法の縦覧状況・届出は無く、キーワード「大規模小売」も0件だった。止めた）**

### （参考）兵庫県 オープンデータカタログ 一覧 6/10

- URL: https://web.pref.hyogo.lg.jp/opendata/index.php?p=6_1&asc=data_link_title&displayedresults=100
- メモ: 2026-09-12に一度見た。924件の一覧に大店立地法の縦覧状況・届出は無く、キーワード「大規模小売」も0件だった。止めた
- **結果: 取りに行かなかった（2026-09-12に一度見た。924件の一覧に大店立地法の縦覧状況・届出は無く、キーワード「大規模小売」も0件だった。止めた）**

### （参考）兵庫県 オープンデータカタログ 一覧 7/10

- URL: https://web.pref.hyogo.lg.jp/opendata/index.php?p=7_1&asc=data_link_title&displayedresults=100
- メモ: 2026-09-12に一度見た。924件の一覧に大店立地法の縦覧状況・届出は無く、キーワード「大規模小売」も0件だった。止めた
- **結果: 取りに行かなかった（2026-09-12に一度見た。924件の一覧に大店立地法の縦覧状況・届出は無く、キーワード「大規模小売」も0件だった。止めた）**

### （参考）兵庫県 オープンデータカタログ 一覧 8/10

- URL: https://web.pref.hyogo.lg.jp/opendata/index.php?p=8_1&asc=data_link_title&displayedresults=100
- メモ: 2026-09-12に一度見た。924件の一覧に大店立地法の縦覧状況・届出は無く、キーワード「大規模小売」も0件だった。止めた
- **結果: 取りに行かなかった（2026-09-12に一度見た。924件の一覧に大店立地法の縦覧状況・届出は無く、キーワード「大規模小売」も0件だった。止めた）**

### （参考）兵庫県 オープンデータカタログ 一覧 9/10

- URL: https://web.pref.hyogo.lg.jp/opendata/index.php?p=9_1&asc=data_link_title&displayedresults=100
- メモ: 2026-09-12に一度見た。924件の一覧に大店立地法の縦覧状況・届出は無く、キーワード「大規模小売」も0件だった。止めた
- **結果: 取りに行かなかった（2026-09-12に一度見た。924件の一覧に大店立地法の縦覧状況・届出は無く、キーワード「大規模小売」も0件だった。止めた）**

### （参考）兵庫県 オープンデータカタログ 一覧 10/10

- URL: https://web.pref.hyogo.lg.jp/opendata/index.php?p=10_1&asc=data_link_title&displayedresults=100
- メモ: 2026-09-12に一度見た。924件の一覧に大店立地法の縦覧状況・届出は無く、キーワード「大規模小売」も0件だった。止めた
- **結果: 取りに行かなかった（2026-09-12に一度見た。924件の一覧に大店立地法の縦覧状況・届出は無く、キーワード「大規模小売」も0件だった。止めた）**

### （参考）兵庫県 オープンデータカタログ キーワード「大規模小売」

- URL: https://web.pref.hyogo.lg.jp/opendata/index.php?keyword=%E5%A4%A7%E8%A6%8F%E6%A8%A1%E5%B0%8F%E5%A3%B2&displayedresults=100
- メモ: 2026-09-12に一度見た。924件の一覧に大店立地法の縦覧状況・届出は無く、キーワード「大規模小売」も0件だった。止めた
- **結果: 取りに行かなかった（2026-09-12に一度見た。924件の一覧に大店立地法の縦覧状況・届出は無く、キーワード「大規模小売」も0件だった。止めた）**

### （参考）兵庫県公報 検索用目録（Excel）

- URL: https://web.pref.hyogo.lg.jp/kk32/pa13_000000105.html
- メモ: 兵庫県公報の目録 Excel（2007年1月〜、年1冊、20冊）。「公告」シートに大店立地法の公告が 2007〜2025 年で 2,032 件（変更 1,262 / 新設 326 / 廃止 48 / 市町の意見 377 ほか）。件名に店舗名は無いが、種類・公告日・担当・公報番号が分かる。koho.py が数える。2015年以降は発行日が Excel の通し番号（2026-09-13に読んだ）
- robots.txt: 許可
- HTTP 200 / utf-8 / 23,779 バイト
- **判定: 表**
- 表 3 個 / PDFリンク 2 本 / Excel 20 本
- いちばん大きい表: 7 行 × 3 列
  - 見出しらしき行: キーワード区分 | 入力するキーワード
  - PDF: 兵庫県公報について、「サイト内検索ボックス」でキーワード検索する具体例はこちら（PDF：31KB） → https://web.pref.hyogo.lg.jp/kk32/documents/000090727_1.pdf
  - PDF: 「兵庫県公報検索ファイル」（Excel形式）による目録の検索方法の説明はこちら（PDF：172KB） → https://web.pref.hyogo.lg.jp/kk32/documents/000090728_1.pdf
  - Excel: 平成19年（1月～12月）公報検索（エクセル：821KB） → https://web.pref.hyogo.lg.jp/kk32/documents/000090298_1.xls
  - Excel: 平成20年（1月～12月）公報検索（エクセル：744KB） → https://web.pref.hyogo.lg.jp/kk32/documents/000093016_1.xls
  - Excel: 平成21年（1月～12月）公報検索（エクセル：839KB） → https://web.pref.hyogo.lg.jp/kk32/documents/000119715_1.xls
  - Excel: 平成22年（1月～12月）公報検索（エクセル：624KB） → https://web.pref.hyogo.lg.jp/kk32/documents/000146501_1.xls
  - Excel: 平成23年（1月～12月）公報検索（エクセル：619KB） → https://web.pref.hyogo.lg.jp/kk32/documents/23-1-12h.xls
- 出てきた言葉: 変更
- 年度らしき表記: 令和2年 / 令和3年 / 令和4年 / 令和5年 / 令和6年 / 令和7年 / 平成19年 / 平成20年

### 兵庫県 まちづくり審議会 大規模小売店舗等立地部会（議案）

- URL: https://web.pref.hyogo.lg.jp/ks21/wd24_000000025.html
- メモ: 部会の議案PDF（第54回〜、2016年〜）の冒頭「届出内容」に、店舗名・所在地・設置者・店舗面積と、その店の届出（過去分も）の届出年月日・条文が載る。parse_bukai.py が pdftotext で読んで届出の記録にする。部会にかかるのは新設と主な変更だけ。「基本計画書」で始まる議案は大規模集客施設条例の計画段階なので今は扱わない。議事録PDFも保存しているが読んでいない
- robots.txt: 許可
- HTTP 200 / utf-8 / 42,136 バイト
- **判定: PDF**
- 表 0 個 / PDFリンク 191 本 / Excel 0 本
  - PDF: 過去審議案件一覧(令和6年度以降)（PDF：217KB） → https://web.pref.hyogo.lg.jp/ks21/documents/151_list.pdf
  - PDF: 議案書（PDF：695KB） → https://web.pref.hyogo.lg.jp/ks21/documents/151_gian.pdf
  - PDF: 議案書（PDF：986KB） → https://web.pref.hyogo.lg.jp/ks21/documents/150_gian.pdf
  - PDF: 議案書（PDF：1,066KB） → https://web.pref.hyogo.lg.jp/ks21/documents/149_gian.pdf
  - PDF: 議案書（PDF：689KB） → https://web.pref.hyogo.lg.jp/ks21/documents/148gian.pdf
- 出てきた言葉: 新設 / 変更
- 年度らしき表記: 令和2年 / 令和3年 / 令和4年 / 令和5年 / 令和6年 / 令和7年 / 令和8年 / 令和9年

### （参考）兵庫県 まちづくり審議会（調査審議の結果）

- URL: https://web.pref.hyogo.lg.jp/ks18/wd20_000000202.html
- メモ: 「大規模小売店舗等立地部会における調査審議の結果（令和7年2月分〜令和8年2月分）」のような年次PDFがある。まず落として形を見る（2026-09-13追加）
- robots.txt: 許可
- HTTP 200 / utf-8 / 73,384 バイト
- **判定: PDF**
- 表 0 個 / PDFリンク 265 本 / Excel 0 本
  - PDF: 議事要旨（PDF：258KB） → https://web.pref.hyogo.lg.jp/ks18/documents/r0702gijiyoushi.pdf
  - PDF: 【資料1-1】「福祉のまちづくり基本方針」の見直しについて（報告）（PDF：145KB）（別ウィンドウで開きます） → https://web.pref.hyogo.lg.jp/ks18/documents/1-1r702.pdf
  - PDF: 【資料1-2】福祉のまちづくり検討小委員会における検討経過（PDF：748KB）（別ウィンドウで開きます） → https://web.pref.hyogo.lg.jp/ks18/documents/1-2r702.pdf
  - PDF: 【資料1-3】前回審議会における主な意見とその対応（PDF：2,129KB）（別ウィンドウで開きます） → https://web.pref.hyogo.lg.jp/ks18/documents/1-3r702.pdf
  - PDF: 【資料1-4】福祉のまちづくり基本方針（改定案）（PDF：1,939KB）（別ウィンドウで開きます） → https://web.pref.hyogo.lg.jp/ks18/documents/1-4r702.pdf
- 出てきた言葉: 変更
- 年度らしき表記: 令和2年 / 令和3年 / 令和4年 / 令和5年 / 令和6年 / 令和7年 / 令和8年 / 平成11年

### （参考）経済産業省 大店立地法の届出状況について

- URL: https://www.meti.go.jp/policy/economy/distribution/daikibo/todokede.html
- メモ: robots.txt で機械の取得が拒否されているので取りに行かない（2026-09-13確認）。内容は政府標準利用規約なので、利用者がブラウザで落とした PDF（ritti_todogai_*.pdf）を data/files/meti/ に置いてもらい、それを読む
- **結果: 取りに行かなかった（robots.txt で機械の取得が拒否されているので取りに行かない（2026-09-13確認）。内容は政府標準利用規約なので、利用者がブラウザで落とした PDF（ritti_todogai_*.pdf）を data/files/meti/ に置いてもらい、それを読む）**

### （参考）日本ショッピングセンター協会 大店立地法新設届出情報

- URL: https://www.jcsc.or.jp/sc_data/sc_open/daitenhou
- メモ: 経産省が経済産業局ごとにまとめた月次の新設届出を転載しているページ。2006年7月分からの月別ページがあり、経産省の公表終了後も更新が続いている。民間団体の一覧なので転載はせず、件数の答え合わせにだけ使う。2023年度までの大元は経産省の PDF（政府標準利用規約）を使う（2026-09-13）
- robots.txt: 許可
- HTTP 200 / UTF-8 / 37,850 バイト
- **判定: わからない**
- 表 0 個 / PDFリンク 1 本 / Excel 0 本
  - PDF: 役員名簿 → https://www.jcsc.or.jp/list/offcer_list.pdf
- 出てきた言葉: 新設 / 届出
- **この先を辿った: 12本** 
  -  2026/08/21 更新 大店立地法新設届出情報 2026年7月 … **表** 18行×7列 PDF1本
  -  2026/07/21 更新 大店立地法新設届出情報 2026年6月 … **表** 45行×7列 PDF1本
  -  2026/06/22 更新 大店立地法新設届出情報 2026年5月 … **表** 48行×7列 PDF1本
  -  2026/05/22 更新 大店立地法新設届出情報 2026年4月 … **表** 50行×7列 PDF1本
  -  2026/04/24 更新 大店立地法新設届出情報 2026年3月 … **表** 62行×7列 PDF1本
  -  2026/03/30 更新 大店立地法新設届出情報 2026年2月 … **表** 52行×7列 PDF1本
  -  2026/03/02 更新 大店立地法新設届出情報 2026年1月 … **表** 37行×7列 PDF1本
  -  2026/01/19 更新 大店立地法新設届出情報 2025年12月 … **表** 54行×7列 PDF1本
  -  2025/12/22 更新 大店立地法新設届出情報 2025年11月 … **表** 38行×7列 PDF1本
  -  2025/11/21 更新 大店立地法新設届出情報 2025年10月 … **表** 45行×7列 PDF1本
  -  2025/10/27 更新 大店立地法新設届出情報 2025年9月 … **表** 55行×7列 PDF1本
  -  2025/09/29 更新 大店立地法新設届出情報 2025年8月 … **表** 41行×7列 PDF1本

### （参考）兵庫県公報 月別一覧

- URL: https://web.pref.hyogo.lg.jp/kk32/pa13_000000081.html
- メモ: 月別一覧。/kk32/koho/YYMM.html が約180か月分並ぶ（古い年は pa13_… のページ）。目録（2007年〜）の公告 1,636 件を本体 PDF までたどる入口（2026-09-13に保存）
- robots.txt: 許可
- HTTP 200 / utf-8 / 25,480 バイト
- **判定: わからない**
- 表 0 個 / PDFリンク 0 本 / Excel 0 本
- 出てきた言葉: 変更
- 年度らしき表記: 令和2年 / 令和3年 / 令和4年 / 令和5年 / 令和6年 / 令和7年 / 令和8年 / 平成18年

### （参考）兵庫県公報 令和5年6月の号一覧

- URL: https://web.pref.hyogo.lg.jp/kk32/koho/202306.html
- メモ: 1か月分のページ。号ごとの PDF は /kk32/koho/documents/YYYYMMDDt.pdf（定期号）・…gN.pdf（号外）。目録の（発行日, 公報番号）→ この一覧の「M月D日第N号」で本体にたどり着ける。公告の本文の形を見るため、廃止（6/13 第421号）と変更（6/20 第423号）の号を1回だけ落とす（2026-09-13）。形は分かったので止めた（本体は koho_pdf.py が読む）
- **結果: 取りに行かなかった（1か月分のページ。号ごとの PDF は /kk32/koho/documents/YYYYMMDDt.pdf（定期号）・…gN.pdf（号外）。目録の（発行日, 公報番号）→ この一覧の「M月D日第N号」で本体にたどり着ける。公告の本文の形を見るため、廃止（6/13 第421号）と変更（6/20 第423号）の号を1回だけ落とす（2026-09-13）。形は分かったので止めた（本体は koho_pdf.py が読む））**

### （参考）兵庫県公報 平成22年12月の号一覧

- URL: https://web.pref.hyogo.lg.jp/kk32/pa13_000000162.html
- メモ: 古い年のページ。号ごとの PDF は /kk32/documents/000NNNNNN.pdf と番号だけで、ラベル「12月3日　第2241号」で見分ける。新設2件・変更2件が載る 12/24 第2247号と、廃止が載る 12/10 第2243号を1回だけ落とす（2026-09-13）。形は分かったので止めた（本体は koho_pdf.py が読む）
- **結果: 取りに行かなかった（古い年のページ。号ごとの PDF は /kk32/documents/000NNNNNN.pdf と番号だけで、ラベル「12月3日　第2241号」で見分ける。新設2件・変更2件が載る 12/24 第2247号と、廃止が載る 12/10 第2243号を1回だけ落とす（2026-09-13）。形は分かったので止めた（本体は koho_pdf.py が読む））**

### （参考）日本SC協会 大店立地法新設届出情報 2026年7月

- URL: https://www.jcsc.or.jp/pt_location/p_20260821_114467
- メモ: 民間の業界団体が集めた一覧なので、そのままの転載や機械での吸い上げはしない（規約と、一覧のまるごと複製を不法行為とした判例への配慮）。兵庫県の件数の答え合わせのためにページを保存するだけ。PDF は落とさない（2026-09-13）
- robots.txt: 許可
- HTTP 200 / UTF-8 / 39,952 バイト
- **判定: 表**
- 表 1 個 / PDFリンク 1 本 / Excel 0 本
- いちばん大きい表: 18 行 × 7 列
  - 見出しらしき行: 大規模小売店舗名 | 所在地 | 建物設置者名 | 小売業者名 | 開店予定 | 店舗面積（㎡）
  - PDF: 役員名簿 → https://www.jcsc.or.jp/list/offcer_list.pdf
- 出てきた言葉: 新設 / 届出 / 店舗面積 / 開店

### （参考）日本SC協会 大店立地法新設届出情報 2014年以前

- URL: https://www.jcsc.or.jp/public_policy/location/index.html
- メモ: 2014年以前の月別ページの入口。転載はしない方針にしたので止めた（2026-09-13）
- **結果: 取りに行かなかった（2014年以前の月別ページの入口。転載はしない方針にしたので止めた（2026-09-13））**

### 兵庫県公報（大規模小売店舗立地法の公告）

- URL: https://web.pref.hyogo.lg.jp/kk32/pa13_000000081.html
- メモ: koho_pdf.py が作る。目録（2007年〜）の公告 1,636 件を、月別一覧→月ページ→号の PDF とたどって本体を読む。公告には店舗名・所在地・設置者・小売業者・店舗面積・新設（変更・廃止）の日・届出年月日・縦覧場所が書いてある。PDF は残さず、大店立地法の公告の部分だけ data/koho/text/ に文字で残す。1回40号ずつ新しいほうから。recon には取りに行かせないので enabled は false（2026-09-13）
- **結果: 取りに行かなかった（koho_pdf.py が作る。目録（2007年〜）の公告 1,636 件を、月別一覧→月ページ→号の PDF とたどって本体を読む。公告には店舗名・所在地・設置者・小売業者・店舗面積・新設（変更・廃止）の日・届出年月日・縦覧場所が書いてある。PDF は残さず、大店立地法の公告の部分だけ data/koho/text/ に文字で残す。1回40号ずつ新しいほうから。recon には取りに行かせないので enabled は false（2026-09-13））**
