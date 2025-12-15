# SQL最適化パターン詳細リファレンス

このドキュメントは、SQL最適化の各パターンについて詳細に解説します。

---

## パターン1: N+1クエリ削減

### 問題の説明

N+1クエリ問題は、親レコードを取得するクエリ（1回）と、各親レコードに対して子レコードを取得するクエリ（N回）を実行することで発生します。データ量が増えると指数関数的に遅くなります。

### 識別方法

- ループ内でSELECT文を実行している
- 同じテーブルに対して異なるWHERE条件で複数回クエリを実行
- アプリケーションログで同じクエリパターンが多数実行されている

### 解決策

**方法1: JOINを使用**
```sql
-- Before: N+1クエリ
SELECT * FROM users;  -- 1回
SELECT * FROM orders WHERE user_id = 1;  -- N回（各ユーザーごと）

-- After: 1回のJOIN
SELECT u.*, o.id as order_id, o.total
FROM users u
LEFT JOIN orders o ON u.id = o.user_id;
```

**方法2: サブクエリで集約**
```sql
SELECT u.*,
  (SELECT COUNT(*) FROM orders WHERE user_id = u.id) as order_count
FROM users u;
-- ※ただし、この方法は大量データでは遅い場合がある
```

**方法3: IN句で一括取得**
```sql
-- ユーザーID一覧を取得
user_ids = [1, 2, 3, ...]

-- 一括で注文を取得
SELECT * FROM orders WHERE user_id IN (1, 2, 3, ...);
-- アプリケーション側でマッピング
```

### 適用場面

- ORM（Sequelize, TypeORM等）を使用している場合に頻発
- マスターデータとトランザクションデータの関連取得
- ユーザー一覧とそれぞれの統計情報を表示

---

## パターン2: インデックス活用

### 問題の説明

WHERE句、JOIN条件、ORDER BY句で使用される列にインデックスがない場合、データベースは全行をスキャン（フルテーブルスキャン）します。これは非常に遅くなります。

### 識別方法

```sql
EXPLAIN SELECT * FROM orders WHERE status = 'completed';
-- type: ALL （フルスキャン）
-- rows: 1000000 （全行スキャン）
```

### 解決策

**単一列インデックス**
```sql
CREATE INDEX idx_orders_status ON orders(status);
```

**複合インデックス（推奨）**
```sql
-- WHERE句で複数列を使用する場合
CREATE INDEX idx_orders_status_created ON orders(status, created_at);

-- 使用例
SELECT * FROM orders
WHERE status = 'completed'  -- インデックスの第1列
AND created_at > '2023-01-01';  -- インデックスの第2列
```

**カバリングインデックス（最速）**
```sql
-- SELECT句の列もインデックスに含める
CREATE INDEX idx_orders_covering ON orders(status, created_at, total);

-- このクエリはインデックスのみで完結（テーブルアクセス不要）
SELECT status, created_at, total
FROM orders
WHERE status = 'completed';
```

### インデックス設計のベストプラクティス

1. **選択性の高い列を優先**: 多様な値を持つ列
2. **WHERE句で頻繁に使用される列**
3. **JOIN条件の列**: 外部キーには必ずインデックス
4. **ORDER BY/GROUP BYで使用される列**
5. **複合インデックスの列順序**: WHERE句で絶対使用される列を先頭に

### 注意事項

- インデックスは書き込み性能に影響（INSERT/UPDATE/DELETE）
- 不要なインデックスは削除
- 統計情報を定期的に更新（ANALYZE TABLE）

---

## パターン3: JOIN最適化

### 問題の説明

不適切なJOIN順序や不要なテーブルのJOINは、大量の中間結果セットを生成し、パフォーマンスを劣化させます。

### 識別方法

```sql
EXPLAIN SELECT ...;
-- rows が大きい値を示している
-- Extra に "Using temporary" や "Using filesort" が表示
```

### 解決策

**方法1: 小さいテーブルを先に結合**
```sql
-- Before: 大きいテーブルから結合
SELECT *
FROM orders o
JOIN users u ON o.user_id = u.id
WHERE u.status = 'active';
-- ordersが100万行、usersが1万行の場合

-- After: 小さいテーブルでフィルタしてから結合
SELECT *
FROM (SELECT * FROM users WHERE status = 'active') u
JOIN orders o ON o.user_id = u.id;
-- または
SELECT *
FROM users u
JOIN orders o ON o.user_id = u.id
WHERE u.status = 'active';
-- ※ オプティマイザが自動的に最適化する場合もある
```

**方法2: 必要な列のみ取得**
```sql
-- Before: すべての列を取得
SELECT * FROM orders o
JOIN users u ON o.user_id = u.id;

-- After: 必要な列のみ
SELECT o.id, o.total, u.name, u.email
FROM orders o
JOIN users u ON o.user_id = u.id;
```

**方法3: 適切なJOINタイプを選択**
```sql
-- INNER JOIN: 両方に存在するレコードのみ
SELECT * FROM orders o
INNER JOIN users u ON o.user_id = u.id;

-- LEFT JOIN: 左側のテーブルのすべてのレコード
SELECT * FROM users u
LEFT JOIN orders o ON u.id = o.user_id;

-- RIGHT JOIN: 右側のテーブルのすべてのレコード（LEFT JOINの逆）
```

### 適用場面

- 複数テーブルを結合するクエリ
- マスターデータとトランザクションデータの結合
- レポート生成クエリ

---

## パターン4: ウィンドウ関数活用

### 問題の説明

複雑な集計やランキングをサブクエリで実装すると、同じテーブルを複数回スキャンすることになり、非効率です。

### 識別方法

- サブクエリが複数ネストしている
- 同じテーブルに対して複数の集計を実行
- ROW_NUMBERやRANKをアプリケーション側で実装

### 解決策

**方法1: ROW_NUMBER()でランキング**
```sql
-- Before: サブクエリで順位を計算
SELECT u.*, (
  SELECT COUNT(*) + 1
  FROM users u2
  WHERE u2.score > u.score
) as rank
FROM users u;

-- After: ウィンドウ関数
SELECT u.*,
  ROW_NUMBER() OVER (ORDER BY score DESC) as rank
FROM users u;
```

**方法2: PARTITION BYでグループ別集計**
```sql
-- Before: 各カテゴリごとにサブクエリ
SELECT p.*, (
  SELECT AVG(price)
  FROM products p2
  WHERE p2.category_id = p.category_id
) as avg_price_in_category
FROM products p;

-- After: ウィンドウ関数
SELECT p.*,
  AVG(price) OVER (PARTITION BY category_id) as avg_price_in_category
FROM products p;
```

**方法3: LAG/LEADで前後の行を参照**
```sql
-- Before: 自己結合で前の行を取得
SELECT t1.date, t1.value,
  t2.value as prev_value,
  t1.value - t2.value as diff
FROM time_series t1
LEFT JOIN time_series t2 ON t1.date = t2.date + INTERVAL 1 DAY;

-- After: LAG関数
SELECT date, value,
  LAG(value) OVER (ORDER BY date) as prev_value,
  value - LAG(value) OVER (ORDER BY date) as diff
FROM time_series;
```

### ウィンドウ関数の種類

- **ROW_NUMBER()**: 行番号（重複なし）
- **RANK()**: ランク（同値は同順位、次は飛ばす）
- **DENSE_RANK()**: ランク（同値は同順位、次は連続）
- **LAG()**: N行前の値
- **LEAD()**: N行後の値
- **FIRST_VALUE()**: パーティション内の最初の値
- **LAST_VALUE()**: パーティション内の最後の値

---

## パターン5: DISTINCT削減

### 問題の説明

DISTINCTは全結果セットをソートまたはハッシュ化して重複を除去するため、コストが高い操作です。

### 識別方法

- クエリにDISTINCTが含まれる
- 重複レコードが返される原因が不明

### 解決策

**方法1: GROUP BYで代替**
```sql
-- Before: DISTINCT
SELECT DISTINCT user_id, MAX(created_at) as last_order
FROM orders;
-- DISTINCTとMAXは矛盾（MAX使用時点でGROUP BY必要）

-- After: GROUP BY
SELECT user_id, MAX(created_at) as last_order
FROM orders
GROUP BY user_id;
```

**方法2: 適切なJOINで重複を防ぐ**
```sql
-- Before: JOINで重複が発生してDISTINCTで除去
SELECT DISTINCT u.name
FROM users u
JOIN orders o ON u.id = o.user_id;

-- After: EXISTSで存在確認
SELECT u.name
FROM users u
WHERE EXISTS (SELECT 1 FROM orders WHERE user_id = u.id);
```

---

## パターン6: EXISTS vs IN

### 問題の説明

サブクエリでINを使用すると、サブクエリの全結果をメモリに保持する必要があります。大量のデータでは非効率です。

### 解決策

```sql
-- Before: IN
SELECT * FROM users
WHERE id IN (SELECT user_id FROM orders WHERE total > 1000);

-- After: EXISTS（推奨）
SELECT * FROM users u
WHERE EXISTS (
  SELECT 1 FROM orders o
  WHERE o.user_id = u.id AND o.total > 1000
);
```

### EXISTSの利点

1. **早期終了**: マッチした時点で検索終了
2. **メモリ効率**: 全結果を保持しない
3. **インデックス活用**: 最適化されやすい

---

## パターン7: LIMIT活用

### 問題の説明

必要な件数以上のデータを取得し、アプリケーション側でフィルタするのは非効率です。

### 解決策

```sql
-- Before: 全件取得してアプリでフィルタ
SELECT * FROM products ORDER BY created_at DESC;
-- アプリで最初の10件のみ使用

-- After: SQLでLIMIT
SELECT * FROM products ORDER BY created_at DESC LIMIT 10;
```

**ページネーション**
```sql
-- ページ2（11-20件目）
SELECT * FROM products
ORDER BY created_at DESC
LIMIT 10 OFFSET 10;
```

---

## パターン8: 計算列のインデックス

### 問題の説明

WHERE句で列に関数を適用すると、インデックスが使用されません。

### 解決策

**方法1: 計算済み列を作成**
```sql
-- Before: インデックス使用不可
SELECT * FROM users WHERE YEAR(created_at) = 2023;

-- After: 範囲検索に変換
SELECT * FROM users
WHERE created_at >= '2023-01-01'
AND created_at < '2024-01-01';
-- created_atにインデックスがあれば使用される
```

**方法2: 生成列（Generated Column）を使用**
```sql
-- 計算済み列を追加
ALTER TABLE users
ADD COLUMN created_year INT AS (YEAR(created_at)) STORED;

-- インデックス作成
CREATE INDEX idx_users_created_year ON users(created_year);

-- クエリ
SELECT * FROM users WHERE created_year = 2023;
-- インデックスが使用される
```

---

## まとめ: 最適化の優先順位

1. **インデックス作成**: 最も効果的で簡単
2. **N+1クエリ削減**: JOINで統合
3. **不要なDISTINCT削除**: GROUP BYやEXISTSで代替
4. **ウィンドウ関数活用**: サブクエリを削減
5. **適切なJOINタイプ**: INNER/LEFT/RIGHT を正しく選択
6. **LIMIT活用**: 必要最小限のデータ取得
7. **EXISTS vs IN**: 大量データではEXISTSを優先
8. **計算列インデックス**: 関数適用を避ける

## 測定と検証

すべての最適化は、以下の手順で効果を検証してください:

1. **最適化前の測定**
   ```sql
   EXPLAIN ANALYZE SELECT ...;
   ```

2. **最適化の適用**

3. **最適化後の測定**
   ```sql
   EXPLAIN ANALYZE SELECT ...;
   ```

4. **比較**
   - 実行時間
   - スキャン行数
   - インデックス使用状況

**目標**: 実行時間50%以上削減、スキャン行数70%以上削減
