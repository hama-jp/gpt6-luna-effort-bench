# 課題: ledgerlite に多通貨対応を追加する

いまいるディレクトリの `ledgerlite` リポジトリで作業してください
(Python 3 の小さな家計簿ツールで、標準ライブラリだけで動きます)。
既存のテストは `python3 -m unittest` で実行できます。

複数の通貨の口座を持つ利用者が増えてきたので、多通貨に対応させます。
次の仕様のとおりに実装してください。

## 1. 読み込み

- `read_statement(path, base="EUR")` にキーワード引数 `base` を追加する。
  これまでの呼び方 `read_statement(path)` もそのまま動くこと。
- banka 形式のファイルには4列目 `Currency` が付くことがある(ヘッダーは
  `Date,Description,Amount,Currency`)。bankb 形式には5列目 `Currency` が付くことがある
  (ヘッダーは `Posted,Payee,Debit,Credit,Currency`)。列のない従来のヘッダーも引き続き有効。
- 列がない、またはセルが空のとき、その取引の通貨は `base` とする。
  通貨コードは大文字小文字を区別せず、大文字で保存する。
- `Transaction` に2つのフィールドを追加する:
  - `currency: str` — ISO の通貨コード(大文字、既定値 `"EUR"`)
  - `original_amount: Decimal | None` — 既定値 `None`
  読み込んだ時点では `amount` はその取引自身の通貨での金額で、`original_amount` は `None` のまま。

## 2. 為替レート — 新しいモジュール `ledgerlite/fx.py`

- `load_rates(path)` はヘッダー `date,currency,rate` の CSV を読む
  (日付は ISO 形式。`rate` = その通貨1単位が基準通貨でいくらか)。通貨コードは大文字小文字を区別しない。
- `convert(transactions, rates, base="EUR")` はすべての取引をその場で基準通貨に換算し、リストを返す:
  - 各取引で `original_amount = amount`(換算前の値)とし、`amount = original_amount × rate` を
    1セント単位に四捨五入(half-up。`models.to_money` を使う)する。`currency` は元の通貨コードのまま。
  - すでに `base` の取引はレート1で、レートの登録は不要。ただし `original_amount` は設定する。
  - 使うレートは取引日のもの。なければ、その通貨の直近の過去のレートを使う。
    ただし取引日から7日前までに限る(7日前は可、8日前は不可)。取引日より後の日付のレートは使わない。
  - 使えるレートがないときは `fx.MissingRateError`(`ValueError` のサブクラス)を送出する。
    メッセージには通貨コードと取引日(ISO 形式 `YYYY-MM-DD`)を含める。
  - `rates` には `load_rates` の戻り値が渡される。

## 3. 重複判定

重複判定は換算の前に行う。通貨が違う2つの取引は、日付・金額・摘要が同じでも重複とみなさない。
それ以外の重複判定の振る舞いは、ドキュメントのとおりのまま変えない。

## 4. レポートと CLI

- `monthly_summary(transactions, year, month, base="EUR")` は結果にキー `"currency": base` を加える。
  それ以外は変えない(換算後の `amount` で集計する)。
- `format_summary` は1行目(`Report YYYY-MM`)のすぐ次に `Currency: <通貨コード>` の行を出力する。
- `report` コマンドに `--base CODE`(既定値 `EUR`)と `--rates PATH` を追加する。
  処理の順番: 読み込み(base 指定つき)→ 重複判定 → 分類 → 換算 → 集計。
- 基準通貨以外の取引があるのに `--rates` が指定されていないときは、`--rates` に触れたエラーを
  標準エラーに出して、終了コード 2 で終わる(トレースバックは出さない)。
- レートが見つからないときは、`MissingRateError` のメッセージを標準エラーに出して、終了コード 2 で終わる
  (トレースバックは出さない)。

## 完了の条件

- 上の仕様がすべて実装され、既存の振る舞いが変わっておらず、`python3 -m unittest` が通る。
- 新しい振る舞いのテストを `tests/` に追加する。
- 外部ライブラリは追加しない。
