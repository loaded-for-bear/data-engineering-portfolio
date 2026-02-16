# 01. CSV基礎（標準ライブラリ）

## 概要

Webサーバーのアクセスログ（CSV）を Python 標準ライブラリのみで集計するスクリプト。
外部ライブラリを使わず、`csv.DictReader` と辞書操作で基本的なデータ処理を行う。

## 使用技術

- Python 標準ライブラリ: `csv`, `io`, `pathlib`
- 辞書によるデータ集計

## 入力データ

- `data/sample.csv` — アクセスログ（endpoint, status, response_time 等）

## 実行方法

```bash
python analyze_logs.py
```

## 処理内容

1. CSVファイルを `csv.DictReader` で読み込み
2. エンドポイント別にリクエスト数・平均レスポンスタイムを集計
3. レスポンスタイムが閾値を超えるスローリクエストを抽出
