# 05. JSON正規化 → SQLite

## 概要

ネストされたJSON（ECサイトの注文データ）を正規化し、SQLiteデータベースに3テーブル構成でロードするETLパイプライン。ロード後にSQLで集計検証を行う。

## 使用技術

- Python標準ライブラリ: `json`, `sqlite3`
- DB正規化（1NF〜3NF）
- 顧客の重複排除
- SQL集計クエリ

## 入力データ

- `data/orders.json` — ネストされた注文データ（顧客情報・注文明細を含む）

## 出力

- `ecommerce.db` — SQLiteデータベース
  - `customers` テーブル
  - `orders` テーブル
  - `order_items` テーブル

## 実行方法

```bash
python etl_json_to_sqlite.py
```

## 処理内容

1. **Extract**: JSONファイルを読み込み、ネスト構造を解析
2. **Transform**: 顧客・注文・注文明細に正規化、顧客の重複排除
3. **Load**: SQLiteにテーブル作成・データ投入
4. **Verify**: 顧客別購入金額・商品別売上ランキングをSQLで検証
