# Excel抽出 実装例

## 例1: 売上データの抽出

```python
# 売上データExcelを読み込み
data = extract_excel('sales-2023.xlsx', output_format='json')

# Sheet1（売上明細）を取得
sales_data = data['Sales']

# データフレームに変換して集計
import pandas as pd
df = pd.DataFrame(sales_data)

# 月別売上を集計
monthly_sales = df.groupby('month')['amount'].sum()
print(monthly_sales)

# 結果をCSVに保存
monthly_sales.to_csv('monthly-sales-summary.csv')
```

## 例2: 在庫データの構造化

```python
# 在庫管理Excelから複数シートを抽出
data = extract_excel('inventory.xlsx')

# 各シートのデータを処理
products = data['Products']  # 商品マスタ
inventory = data['Inventory']  # 在庫数
locations = data['Locations']  # 保管場所

# JSONファイルに保存（API連携用）
import json
with open('inventory-data.json', 'w', encoding='utf-8') as f:
    json.dump({
        'products': products,
        'inventory': inventory,
        'locations': locations
    }, f, ensure_ascii=False, indent=2)

print(f"✅ 商品数: {len(products)}件")
print(f"✅ 在庫レコード: {len(inventory)}件")
```

## 例3: 大容量Excelの処理

```python
# 大容量Excel（100万行以上）を効率的に処理
def process_large_excel(file_path, chunk_size=10000):
    # チャンクごとに読み込み
    for chunk in pd.read_excel(file_path, chunksize=chunk_size):
        # データ処理
        process_chunk(chunk)

        # メモリ解放
        del chunk

def process_chunk(df):
    # チャンクごとの処理（集計、変換等）
    summary = df.groupby('category')['value'].sum()
    # データベースに保存等
    save_to_database(summary)

# 実行
process_large_excel('large-data.xlsx')
```

## 例4: 複数ファイルの一括処理

```python
import glob
import pandas as pd

# 複数のExcelファイルを一括処理
all_data = []
for file_path in glob.glob('data/*.xlsx'):
    data = extract_excel(file_path)
    all_data.append(data)

# 結合して出力
combined = pd.concat([pd.DataFrame(d['Sheet1']) for d in all_data])
combined.to_csv('combined-data.csv', index=False)
```

## 例5: 書式情報付き抽出

```python
from openpyxl import load_workbook

def extract_with_formatting(file_path):
    wb = load_workbook(file_path)
    ws = wb.active

    data = []
    for row in ws.iter_rows(min_row=2):  # ヘッダー行をスキップ
        row_data = {}
        for cell in row:
            row_data[cell.column_letter] = {
                'value': cell.value,
                'font_bold': cell.font.bold,
                'fill_color': cell.fill.fgColor.rgb if cell.fill.fgColor else None
            }
        data.append(row_data)

    return data
```
