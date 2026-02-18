# uuid — 一意識別子の生成（標準ライブラリ）

## 概要

Python 標準ライブラリ。RFC 4122 準拠の UUID（Universally Unique Identifier）を生成する。
外部ライブラリ不要で、テストデータの ID 生成やデータベースの主キーに使える。

## 基本構文

```python
import uuid

# UUID v4（ランダム生成）— 最もよく使う
uid = uuid.uuid4()
print(uid)        # → a3b2c1d4-e5f6-7890-abcd-ef1234567890
print(str(uid))   # → 文字列変換（CSV出力時などに使う）
print(uid.hex)    # → ハイフンなし "a3b2c1d4e5f67890abcdef1234567890"
```

## UUID のバージョン

| バージョン | 生成方法 | 用途 |
|-----------|---------|------|
| `uuid1()` | MACアドレス + タイムスタンプ | 時刻順でソート可能。ただしMAC漏洩リスクあり |
| `uuid3(namespace, name)` | 名前ベース（MD5） | 同じ入力なら同じUUID。決定的 |
| **`uuid4()`** | **ランダム** | **最も一般的。テストデータ・主キー向け** |
| `uuid5(namespace, name)` | 名前ベース（SHA-1） | uuid3 の SHA-1 版。より安全 |

```python
# uuid1: タイムスタンプベース
uuid.uuid1()  # → 時刻+MAC由来

# uuid3/uuid5: 名前ベース（同じ入力 → 同じ出力）
uuid.uuid3(uuid.NAMESPACE_DNS, "example.com")
uuid.uuid5(uuid.NAMESPACE_DNS, "example.com")

# uuid4: ランダム（毎回異なる）
uuid.uuid4()
```

## 大量生成

```python
import uuid

# リスト内包表記で大量生成
n = 500_000
order_ids = [str(uuid.uuid4()) for _ in range(n)]
```

### パフォーマンス

```
100,000件: 約0.2秒
500,000件: 約1.1秒
```

大量生成でも十分高速。50万件程度なら問題にならない。

## 再現性（シード固定）

`uuid4()` はランダムなので **シード固定できない**。
テストで再現性が必要な場合は `random` モジュールで代替する:

```python
import random

random.seed(42)

def reproducible_uuid():
    """再現可能なUUID風文字列を生成"""
    return f"{random.getrandbits(128):032x}"

# フォーマットを合わせたい場合
def reproducible_uuid_formatted():
    h = f"{random.getrandbits(128):032x}"
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}"
```

## よくある使い方

### テストデータ生成（pandas と組み合わせ）

```python
import uuid
import numpy as np
import pandas as pd

n = 500_000
df = pd.DataFrame({
    "order_id": [str(uuid.uuid4()) for _ in range(n)],
    "quantity": np.random.randint(1, 101, size=n),
})
```

### 文字列フォーマット変換

```python
uid = uuid.uuid4()

str(uid)          # "a3b2c1d4-e5f6-7890-abcd-ef1234567890"（ハイフンあり）
uid.hex           # "a3b2c1d4e5f67890abcdef1234567890"（ハイフンなし）
uid.int           # 整数表現
uid.bytes         # 16バイトのバイト列
```

### 文字列から UUID オブジェクトに変換

```python
uid = uuid.UUID("a3b2c1d4-e5f6-7890-abcd-ef1234567890")
uid = uuid.UUID("a3b2c1d4e5f67890abcdef1234567890")  # ハイフンなしも可
```

## faker との比較

UUID 生成だけなら **uuid 標準ライブラリの方が速い**:

```
uuid.uuid4()  x 100,000: 0.225s
faker.uuid4() x 100,000: 0.300s
```

faker は人名・住所など「リアルなダミーデータ」が必要な場合に使う。
UUID だけなら標準ライブラリで十分。→ 詳細: [faker.md](./faker.md)
