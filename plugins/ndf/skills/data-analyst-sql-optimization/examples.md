# SQL最適化 Before/After 実例集

このドキュメントは、実際のプロジェクトで適用されたSQL最適化の具体例を紹介します。

---

## 例1: ECサイトの注文一覧ページ

### シナリオ

ECサイトの管理画面で、ユーザーごとの注文一覧を表示する。各ユーザーの注文件数と合計金額も表示したい。

### Before（N+1クエリ）

```sql
-- ユーザー一覧を取得（1回）
SELECT * FROM users LIMIT 100;

-- 各ユーザーの注文件数を取得（100回）
SELECT COUNT(*) FROM orders WHERE user_id = 1;
SELECT COUNT(*) FROM orders WHERE user_id = 2;
...
SELECT COUNT(*) FROM orders WHERE user_id = 100;

-- 各ユーザーの注文合計金額を取得（100回）
SELECT SUM(total) FROM orders WHERE user_id = 1;
SELECT SUM(total) FROM orders WHERE user_id = 2;
...
SELECT SUM(total) FROM orders WHERE user_id = 100;
```

**問題点**:
- クエリ実行回数: 1 + 100 + 100 = 201回
- 実行時間: 約5秒（ユーザー数が増えると指数関数的に増加）

### After（1回のJOINで統合）

```sql
SELECT
  u.id,
  u.name,
  u.email,
  COUNT(o.id) as order_count,
  COALESCE(SUM(o.total), 0) as order_total
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.name, u.email
LIMIT 100;
```

**改善結果**:
- クエリ実行回数: 1回
- 実行時間: 約0.2秒（25倍高速化）
- スキャン行数: 大幅に削減

---

## 例2: 検索機能のパフォーマンス改善

### シナリオ

商品検索で、カテゴリと価格帯でフィルタリングする。検索が遅いとユーザーから苦情が来ている。

### Before（インデックスなし）

```sql
SELECT * FROM products
WHERE category = 'Electronics'
AND price BETWEEN 1000 AND 5000
ORDER BY created_at DESC
LIMIT 20;
```

```sql
-- 実行計画
EXPLAIN SELECT ...;
-- type: ALL （フルスキャン）
-- rows: 1000000 （全商品をスキャン）
-- Extra: Using where; Using filesort
```

**問題点**:
- 実行時間: 約3秒
- 100万商品すべてをスキャン
- ソートに時間がかかる

### After（適切なインデックス作成）

```sql
-- 複合インデックス作成
CREATE INDEX idx_products_category_price_created
ON products(category, price, created_at DESC);

-- 同じクエリ
SELECT * FROM products
WHERE category = 'Electronics'
AND price BETWEEN 1000 AND 5000
ORDER BY created_at DESC
LIMIT 20;
```

```sql
-- 実行計画（改善後）
EXPLAIN SELECT ...;
-- type: range （範囲スキャン）
-- rows: 5000 （フィルタ後の行数）
-- Extra: Using index condition （インデックス使用）
```

**改善結果**:
- 実行時間: 約0.05秒（60倍高速化）
- スキャン行数: 1,000,000 → 5,000（200倍削減）
- インデックスのみで完結

---

## 例3: レポート生成の高速化

### シナリオ

月次レポートで、各商品カテゴリの売上ランキングを生成する。複雑なサブクエリで実装されており、実行に10分以上かかる。

### Before（サブクエリの入れ子）

```sql
SELECT
  p.id,
  p.name,
  p.category,
  (SELECT SUM(oi.quantity * oi.price)
   FROM order_items oi
   WHERE oi.product_id = p.id
   AND oi.created_at >= '2023-01-01'
   AND oi.created_at < '2023-02-01') as monthly_revenue,
  (SELECT COUNT(DISTINCT o.user_id)
   FROM orders o
   JOIN order_items oi ON o.id = oi.order_id
   WHERE oi.product_id = p.id
   AND o.created_at >= '2023-01-01'
   AND o.created_at < '2023-02-01') as unique_buyers,
  (SELECT COUNT(*)
   FROM order_items oi2
   WHERE oi2.product_id = p.id
   AND oi2.created_at >= '2023-01-01'
   AND oi2.created_at < '2023-02-01') as order_count
FROM products p
ORDER BY monthly_revenue DESC;
```

**問題点**:
- 各商品ごとに3つのサブクエリを実行（N × 3回スキャン）
- 実行時間: 約10分
- サブクエリが独立しているため最適化されない

### After（1回のJOIN + ウィンドウ関数）

```sql
WITH monthly_stats AS (
  SELECT
    p.id as product_id,
    p.name,
    p.category,
    SUM(oi.quantity * oi.price) as monthly_revenue,
    COUNT(DISTINCT o.user_id) as unique_buyers,
    COUNT(oi.id) as order_count
  FROM products p
  LEFT JOIN order_items oi ON p.id = oi.product_id
    AND oi.created_at >= '2023-01-01'
    AND oi.created_at < '2023-02-01'
  LEFT JOIN orders o ON oi.order_id = o.id
  GROUP BY p.id, p.name, p.category
)
SELECT
  *,
  ROW_NUMBER() OVER (PARTITION BY category ORDER BY monthly_revenue DESC) as rank_in_category,
  PERCENT_RANK() OVER (ORDER BY monthly_revenue DESC) as revenue_percentile
FROM monthly_stats
ORDER BY monthly_revenue DESC;
```

**改善結果**:
- 実行時間: 約10秒（60倍高速化）
- スキャン回数: N × 3回 → 1回のJOIN
- ウィンドウ関数でカテゴリ別ランキングも追加

---

## 例4: ダッシュボードの集計クエリ

### シナリオ

管理ダッシュボードで、最近30日間の日別売上、累計売上、前日比を表示する。

### Before（自己結合で前日の値を取得）

```sql
SELECT
  t1.date,
  t1.daily_sales,
  t2.daily_sales as prev_day_sales,
  t1.daily_sales - t2.daily_sales as diff,
  (SELECT SUM(daily_sales)
   FROM daily_sales_summary t3
   WHERE t3.date <= t1.date
   ORDER BY date) as cumulative_sales
FROM daily_sales_summary t1
LEFT JOIN daily_sales_summary t2
  ON t1.date = DATE_ADD(t2.date, INTERVAL 1 DAY)
WHERE t1.date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
ORDER BY t1.date;
```

**問題点**:
- 自己結合でデータ量が増大
- 累計売上のサブクエリが各行で実行される
- 実行時間: 約2秒

### After（ウィンドウ関数で簡潔に）

```sql
SELECT
  date,
  daily_sales,
  LAG(daily_sales) OVER (ORDER BY date) as prev_day_sales,
  daily_sales - LAG(daily_sales) OVER (ORDER BY date) as diff,
  SUM(daily_sales) OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as cumulative_sales
FROM daily_sales_summary
WHERE date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
ORDER BY date;
```

**改善結果**:
- 実行時間: 約0.1秒（20倍高速化）
- 自己結合不要
- サブクエリ不要
- コードが読みやすい

---

## 例5: 重複ユーザーの検出

### シナリオ

同じメールアドレスを持つユーザーを検出し、重複を解消する。

### Before（DISTINCT + サブクエリ）

```sql
SELECT DISTINCT u1.*
FROM users u1
WHERE u1.email IN (
  SELECT email
  FROM users
  GROUP BY email
  HAVING COUNT(*) > 1
);
```

**問題点**:
- DISTINCTで重複除去のコスト
- サブクエリの実行コスト
- 実行時間: 約5秒

### After（ウィンドウ関数で重複識別）

```sql
WITH ranked_users AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY email ORDER BY created_at ASC) as rn,
    COUNT(*) OVER (PARTITION BY email) as duplicate_count
  FROM users
)
SELECT *
FROM ranked_users
WHERE duplicate_count > 1
ORDER BY email, rn;
```

**改善結果**:
- 実行時間: 約0.5秒（10倍高速化）
- 重複の順序も明確（最初に登録されたユーザーが特定可能）
- duplicate_countで重複数もわかる

**重複削除（最初の1件のみ残す）**:
```sql
WITH ranked_users AS (
  SELECT
    id,
    ROW_NUMBER() OVER (PARTITION BY email ORDER BY created_at ASC) as rn
  FROM users
)
DELETE FROM users
WHERE id IN (
  SELECT id FROM ranked_users WHERE rn > 1
);
```

---

## 例6: ページネーションの最適化

### シナリオ

ブログ記事一覧で、ページネーション（1ページ20件）を実装。後半のページが非常に遅い。

### Before（OFFSET使用）

```sql
-- ページ1000（19980-19999件目）
SELECT * FROM posts
ORDER BY created_at DESC
LIMIT 20 OFFSET 19980;
```

**問題点**:
- OFFSETは指定した行数をスキップするため、19980行を読み込んでから20行を返す
- 後半ページほど遅くなる
- 実行時間: ページ1で0.05秒、ページ1000で3秒

### After（カーソルベースページネーション）

```sql
-- ページ1
SELECT * FROM posts
ORDER BY created_at DESC, id DESC
LIMIT 20;
-- 最後の行のcreated_atとidを記録: ('2023-01-15 10:30:00', 12345)

-- ページ2
SELECT * FROM posts
WHERE (created_at, id) < ('2023-01-15 10:30:00', 12345)
ORDER BY created_at DESC, id DESC
LIMIT 20;
-- 最後の行を記録して続ける
```

```sql
-- インデックス（created_at, idの複合インデックス）
CREATE INDEX idx_posts_created_id ON posts(created_at DESC, id DESC);
```

**改善結果**:
- 実行時間: すべてのページで約0.05秒（ページ1000でも高速）
- スキップせずに直接必要な行から取得
- ユーザー体験が大幅に向上

**注意点**:
- 「ページ番号」ではなく「次へ/前へ」のナビゲーションになる
- ページ番号が必須の場合はOFFSETを使用（またはページ番号を制限）

---

## 例7: 複数テーブルのJOIN順序最適化

### シナリオ

注文データに、ユーザー、商品、配送情報を結合してレポート生成。クエリが非常に遅い。

### Before（大きいテーブルから結合）

```sql
SELECT
  o.id,
  u.name,
  p.name as product_name,
  s.status as shipping_status
FROM orders o
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
JOIN users u ON o.user_id = u.id
JOIN shipments s ON o.id = s.order_id
WHERE o.created_at >= '2023-01-01';
```

**問題点**:
- ordersから開始するため、大量の中間結果セット
- 実行時間: 約8秒

### After（小さいテーブル、絞り込み条件を先に）

```sql
-- CTEで段階的にフィルタ
WITH recent_orders AS (
  SELECT id, user_id
  FROM orders
  WHERE created_at >= '2023-01-01'
),
order_details AS (
  SELECT
    ro.id as order_id,
    ro.user_id,
    oi.product_id
  FROM recent_orders ro
  JOIN order_items oi ON ro.id = oi.order_id
)
SELECT
  od.order_id,
  u.name,
  p.name as product_name,
  s.status as shipping_status
FROM order_details od
JOIN users u ON od.user_id = u.id
JOIN products p ON od.product_id = p.id
JOIN shipments s ON od.order_id = s.order_id;
```

```sql
-- 必要なインデックス
CREATE INDEX idx_orders_created ON orders(created_at);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_shipments_order_id ON shipments(order_id);
```

**改善結果**:
- 実行時間: 約0.8秒（10倍高速化）
- 先にフィルタすることで中間結果セットを削減
- 段階的な処理で可読性も向上

---

## 例8: 集計関数とDISTINCT

### シナリオ

各カテゴリで購入したユニークユーザー数をカウントする。

### Before（DISTINCT + サブクエリ）

```sql
SELECT
  c.name as category,
  (SELECT COUNT(DISTINCT o.user_id)
   FROM orders o
   JOIN order_items oi ON o.id = oi.order_id
   JOIN products p ON oi.product_id = p.id
   WHERE p.category_id = c.id) as unique_buyers
FROM categories c;
```

**問題点**:
- 各カテゴリごとにサブクエリ実行
- 実行時間: 約6秒

### After（1回のJOIN + GROUP BY）

```sql
SELECT
  c.name as category,
  COUNT(DISTINCT o.user_id) as unique_buyers
FROM categories c
LEFT JOIN products p ON c.id = p.category_id
LEFT JOIN order_items oi ON p.id = oi.product_id
LEFT JOIN orders o ON oi.order_id = o.id
GROUP BY c.id, c.name;
```

**改善結果**:
- 実行時間: 約0.5秒（12倍高速化）
- 1回のJOINで完結

---

## まとめ: 実例から学ぶポイント

1. **N+1クエリは必ずJOINに統合**: 例1, 例7
2. **インデックスは必須**: 例2, 例6
3. **ウィンドウ関数で複雑なサブクエリを削減**: 例3, 例4, 例5
4. **ページネーションはカーソルベースが高速**: 例6
5. **JOIN順序を意識**: 例7
6. **DISTINCTは極力避ける**: 例5, 例8
7. **CTEで段階的に処理**: 例7

## 測定の重要性

すべての最適化は、以下のステップで効果を確認してください:

1. **Before測定**: EXPLAIN ANALYZE で実行計画と時間を記録
2. **最適化適用**: パターンに従って改善
3. **After測定**: 同じ方法で測定
4. **比較**: 改善率を算出（実行時間、スキャン行数）

**目標値**:
- 実行時間: 50%以上削減
- スキャン行数: 70%以上削減
- ユーザー体験: 体感で「遅い」→「速い」になること
