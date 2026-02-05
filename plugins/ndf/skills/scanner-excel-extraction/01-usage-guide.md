# Excel抽出 使用ガイド

## スクリプト詳細

### extract-excel.py

Excelファイルを読み込み、構造化されたデータに変換します。

**コード概要**:
```python
import pandas as pd
import json

def extract_excel(file_path, output_format='json', evaluate_formulas=False):
    # Excelファイルを読み込み
    excel_file = pd.ExcelFile(file_path)

    data = {}
    for sheet_name in excel_file.sheet_names:
        # 各シートを読み込み
        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            # 数式を評価するかどうか
            engine='openpyxl' if evaluate_formulas else 'xlrd'
        )

        if output_format == 'json':
            # JSON形式に変換
            data[sheet_name] = df.to_dict(orient='records')
        elif output_format == 'csv':
            # CSV形式で保存
            df.to_csv(f'{file_path.stem}_{sheet_name}.csv', index=False)

    if output_format == 'json':
        # JSONファイルに保存
        with open(f'{file_path.stem}.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return data
```

### convert-to-json.js (Node.js版)

```javascript
const XLSX = require('xlsx');
const fs = require('fs');

function extractExcel(filePath) {
  // Excelファイルを読み込み
  const workbook = XLSX.readFile(filePath);

  const data = {};

  // 各シートを処理
  workbook.SheetNames.forEach(sheetName => {
    const sheet = workbook.Sheets[sheetName];
    // JSONに変換
    data[sheetName] = XLSX.utils.sheet_to_json(sheet);
  });

  return data;
}
```

## データ型の扱い

### 日付

```python
# 日付を正しく読み込む
df = pd.read_excel('data.xlsx', parse_dates=['date_column'])

# 日付フォーマット変換
df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
```

### 数値

```python
# 数値として読み込む（カンマ区切りの数値対応）
df['amount'] = df['amount'].str.replace(',', '').astype(float)
```

### 文字列

```python
# 前後の空白を削除
df['name'] = df['name'].str.strip()
```

## トラブルシューティング

### Q: 日付が数値になってしまう

A: Excelの日付シリアル値です。変換が必要:
```python
df['date'] = pd.to_datetime(df['date'], unit='D', origin='1899-12-30')
```

### Q: 日本語が文字化けする

A: エンコーディングを指定:
```python
df = pd.read_excel('data.xlsx', encoding='utf-8')
```

### Q: メモリ不足エラー

A: チャンク処理を使用:
```python
for chunk in pd.read_excel('large.xlsx', chunksize=10000):
    process(chunk)
```

### Q: 数式が評価されない

A: openpyxlエンジンを使用:
```python
df = pd.read_excel('data.xlsx', engine='openpyxl')
```
