---
name: scanner-excel-extraction
description: |
  Extract, transform, and structure data from Excel files including multiple sheets, formulas, and formatting. Use when processing Excel data or converting to other formats.

  This skill provides Excel data extraction:
  - Multiple sheet reading
  - Data structuring (JSON/CSV conversion)
  - Formula evaluation
  - Large file handling with chunking

  Triggers: "extract Excel data", "read spreadsheet", "convert Excel to JSON", "convert Excel to CSV", "Excel解析", "スプレッドシート処理", "データ抽出"
allowed-tools:
  - Bash
  - Write
---

# Scanner Excel Extraction Skill

## 概要

scannerエージェントがExcelファイルからデータを抽出し、構造化されたフォーマット（JSON、CSV）に変換する際に使用します。

## クイックリファレンス

### 基本コマンド

```bash
# 全シートをJSONに変換
python scripts/extract-excel.py data.xlsx --output=json

# 特定シートのみCSVに変換
python scripts/extract-excel.py data.xlsx --sheet="Sheet1" --output=csv

# 数式を評価して出力
python scripts/extract-excel.py data.xlsx --evaluate-formulas
```

### 出力形式

**JSON形式**:
```json
{
  "Sheet1": [
    {"id": 1, "name": "Product A", "price": 1000}
  ]
}
```

**CSV形式**: 各シートごとに `data_Sheet1.csv`, `data_Sheet2.csv` を生成

### 必要なライブラリ

```bash
pip install pandas openpyxl xlrd
```

## ベストプラクティス

| DO | DON'T |
|----|-------|
| ヘッダー行を明確に（1行目） | 複雑な書式に依存 |
| データ型を統一 | 結合セルを使用 |
| 大容量ファイルはチャンク処理 | 全データをメモリに展開 |
| 空白セルの扱いを定義 | マクロに依存 |

## 詳細ガイド

| ファイル | 内容 |
|---------|------|
| `01-usage-guide.md` | 詳細な使用方法、スクリプト実装、データ型の扱い |
| `02-examples.md` | 実装例（売上データ、在庫データ、大容量ファイル） |

## 関連Skill

- **scanner-pdf-analysis**: PDF解析
- **data-analyst-export**: データエクスポート
