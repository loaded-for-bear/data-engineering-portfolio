# logging モジュール

## 基本設定

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)
```

## ログレベル

| レベル | 用途 |
|--------|------|
| `DEBUG` | 開発中の詳細情報 |
| `INFO` | 正常な処理の記録 |
| `WARNING` | 注意が必要な事象 |
| `ERROR` | エラー発生 |
| `CRITICAL` | 致命的なエラー |

- `basicConfig(level=logging.INFO)` → INFO以上を出力（DEBUG は出ない）

## 使い方

```python
logger.info("処理を開始します")
logger.info(f"取得件数: {count}件")
logger.warning("欠損値があります")
logger.error(f"API呼び出し失敗: {e}")
```

## f-string vs % スタイル

```python
# f-string（シンプルで読みやすい）
logger.info(f"取得件数: {count}件")

# % スタイル（遅延評価でパフォーマンスが良い）
logger.info("取得件数: %d件", count)
```

- DEBUGログが大量にある場合は % スタイルの方が効率的（level未満なら文字列生成をスキップ）
- 通常のスクリプトでは f-string で十分

## ファイルにも出力する場合

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),                    # コンソール出力
        logging.FileHandler("etl.log", encoding="utf-8"),  # ファイル出力
    ]
)
```
