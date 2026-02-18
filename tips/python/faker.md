# Faker — テストデータ生成ライブラリ

## 概要

リアルなダミーデータ（人名・住所・メール・日時など）を簡単に生成できる Python ライブラリ。
テスト・開発・デモ用データの作成に使う。

## インストール

```bash
pip install faker
```

## 基本構文

```python
from faker import Faker

fake = Faker()          # 英語（デフォルト）
fake = Faker("ja_JP")   # 日本語ロケール

fake.name()             # "田中 太郎"
fake.email()            # "tanaka@example.com"
fake.address()          # "東京都渋谷区..."
fake.phone_number()     # "090-1234-5678"
fake.uuid4()            # "a3b2c1d4-e5f6-..."
fake.date_time()        # datetime(2026, 2, 18, 14, 30, 0)
fake.text(max_nb_chars=50)  # ランダムなテキスト
```

## よく使うプロバイダ

### 個人情報系

```python
fake.name()              # フルネーム
fake.first_name()        # 名
fake.last_name()         # 姓
fake.email()             # メールアドレス
fake.phone_number()      # 電話番号
fake.company()           # 会社名
fake.job()               # 職種
```

### 日時系

```python
fake.date_time()                            # ランダムな日時
fake.date_between(start_date="-1y")         # 過去1年以内の日付
fake.date_time_between(                     # 範囲指定
    start_date="-30d", end_date="now"
)
fake.iso8601()                              # ISO 8601 形式文字列
```

### 数値・ID系

```python
fake.uuid4()                    # UUID
fake.random_int(min=1, max=100) # ランダム整数
fake.pyfloat(min_value=1.0, max_value=999.99, right_digits=2)  # 小数
fake.bothify("C######")        # パターン指定（C + 6桁数字）
fake.numerify("P#####")        # 数字のみ置換（P + 5桁数字）
```

### 住所・地理系

```python
fake.address()           # 完全な住所
fake.city()              # 市区町村
fake.prefecture()        # 都道府県（ja_JP）
fake.zipcode()           # 郵便番号
fake.latitude()          # 緯度
fake.longitude()         # 経度
```

## シード固定（再現性の確保）

```python
Faker.seed(42)           # グローバルシード
fake = Faker()
fake.seed_instance(42)   # インスタンスシード

# 同じシードなら毎回同じデータが生成される
```

## 大量データ生成

### 基本: リスト内包表記

```python
# 1,000件のダミーデータ
data = [
    {
        "name": fake.name(),
        "email": fake.email(),
        "city": fake.city(),
    }
    for _ in range(1000)
]
df = pd.DataFrame(data)
```

### ユニーク値の保証

```python
# unique を使うと重複しない値を生成
names = [fake.unique.name() for _ in range(100)]

# リセット（ユニークプールをクリア）
fake.unique.clear()
```

## numpy / random との比較・使い分け

| 用途 | faker | numpy / random |
|------|-------|---------------|
| 人名・住所・メール | **最適** | 自力で作る必要あり |
| 固定リストから選択 | `fake.random_element()` | `np.random.choice()` の方が速い |
| 数値（大量） | `fake.random_int()` → **遅い** | `np.random.randint()` → **速い** |
| 50万件以上 | 数十秒〜数分 | 数秒 |
| 依存 | `pip install faker` | 標準 or numpy のみ |

### 使い分けの指針

```
リアルな個人情報（名前・住所・メール）が必要 → faker
数値・固定リスト中心 + 大量生成 → numpy / random
両方必要 → 組み合わせる（下記）
```

### 組み合わせ例

```python
import numpy as np
from faker import Faker

fake = Faker("ja_JP")
n = 100_000

df = pd.DataFrame({
    # faker: リアルなデータが必要なカラム
    "customer_name": [fake.name() for _ in range(n)],
    "email": [fake.email() for _ in range(n)],

    # numpy: 数値・固定リスト（高速）
    "quantity": np.random.randint(1, 101, size=n),
    "category": np.random.choice(["A", "B", "C"], size=n),
})
```

## パフォーマンスの注意点

- faker は **1件ずつ Python で生成** するため、大量データでは遅い
- 10万件を超える場合は、faker が必要なカラムだけ faker を使い、残りは numpy にする
- `fake.unique` は内部で set を保持するため、大量生成でメモリが増加する
- ロケール（`ja_JP` 等）を指定すると、デフォルト（`en_US`）より若干遅くなる
