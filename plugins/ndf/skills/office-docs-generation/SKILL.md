---
name: office-docs-generation
description: Word (.docx), PowerPoint (.pptx), Excel (.xlsx) ファイルをPython標準ライブラリ（python-docx, python-pptx, openpyxl）で新規作成・編集するためのガイド。調査結果や分析データをOffice形式に出力したい場合に使用。Do NOT use for reading/extracting — use scanner agent or Read tool instead.
Triggers: "docx 生成", "Word作成", "pptx 生成", "PowerPoint作成", "xlsx 生成", "Excel出力", "レポート作成 Word", "スライド生成", "create docx", "create pptx", "create xlsx", "generate excel", "generate report"
---

# Office文書生成ガイド

Word/PowerPoint/Excel ファイルを**新規作成・編集**するためのPythonライブラリ使用ガイド。既存ファイルの**読み取り・抽出**は対象外（scanner エージェントか Read tool を使う）。

## 使用ライブラリ

| 用途 | ライブラリ | インストール |
|---|---|---|
| .docx 作成・編集 | python-docx | `pip install python-docx` |
| .pptx 作成・編集 | python-pptx | `pip install python-pptx` |
| .xlsx 作成・編集 | openpyxl | `pip install openpyxl` |
| .xlsx + 数式/チャート強化 | openpyxl + pandas | `pip install openpyxl pandas` |

プロジェクトで `uv` / `poetry` を使っていればそれに合わせる。

## Word (.docx)

### 基本パターン

```python
from docx import Document
from docx.shared import Pt, Cm, RGBColor

doc = Document()

# 見出し
doc.add_heading('タイトル', level=1)
doc.add_heading('セクション', level=2)

# 段落
p = doc.add_paragraph('通常テキスト ')
p.add_run('太字').bold = True
p.add_run(' と ')
p.add_run('斜体').italic = True

# リスト
doc.add_paragraph('項目1', style='List Bullet')
doc.add_paragraph('項目2', style='List Bullet')

# 表
table = doc.add_table(rows=3, cols=2)
table.style = 'Light Grid Accent 1'
hdr = table.rows[0].cells
hdr[0].text = '項目'
hdr[1].text = '値'

# ページ区切り
doc.add_page_break()

# 画像
doc.add_picture('path/to/image.png', width=Cm(10))

doc.save('output.docx')
```

### 既存文書の編集

```python
doc = Document('existing.docx')
for para in doc.paragraphs:
    if '{{PLACEHOLDER}}' in para.text:
        para.text = para.text.replace('{{PLACEHOLDER}}', '実際の値')
doc.save('edited.docx')
```

### スタイル設定

```python
style = doc.styles['Normal']
style.font.name = 'Yu Gothic'
style.font.size = Pt(10)
```

## PowerPoint (.pptx)

### 基本パターン

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

prs = Presentation()

# タイトルスライド
slide = prs.slides.add_slide(prs.slide_layouts[0])
slide.shapes.title.text = 'プレゼンタイトル'
slide.placeholders[1].text = 'サブタイトル'

# 箇条書きスライド
slide = prs.slides.add_slide(prs.slide_layouts[1])
slide.shapes.title.text = 'ポイント'
body = slide.placeholders[1].text_frame
body.text = '第1ポイント'
p = body.add_paragraph()
p.text = '第2ポイント'
p.level = 0

# 画像スライド
slide = prs.slides.add_slide(prs.slide_layouts[6])  # 空白レイアウト
slide.shapes.add_picture('chart.png', Inches(1), Inches(1), width=Inches(8))

# 表スライド
slide = prs.slides.add_slide(prs.slide_layouts[6])
rows, cols = 4, 3
left = top = Inches(1)
width = Inches(8)
height = Inches(4)
table = slide.shapes.add_table(rows, cols, left, top, width, height).table
table.cell(0, 0).text = '項目'
table.cell(0, 1).text = '値1'
table.cell(0, 2).text = '値2'

# スピーカーノート
slide.notes_slide.notes_text_frame.text = '発表者メモ'

prs.save('output.pptx')
```

### テンプレート使用

```python
prs = Presentation('template.pptx')
# 既存スライドを複製・編集
```

## Excel (.xlsx)

### 基本パターン（openpyxl直接使用）

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

wb = Workbook()
ws = wb.active
ws.title = 'データ'

# ヘッダー
headers = ['日付', 'ユーザー', '金額']
for col, h in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col, value=h)
    cell.font = Font(bold=True, color='FFFFFF')
    cell.fill = PatternFill('solid', fgColor='4472C4')
    cell.alignment = Alignment(horizontal='center')

# データ
rows = [
    ('2026-04-23', 'alice', 1200),
    ('2026-04-23', 'bob', 3400),
]
for row in rows:
    ws.append(row)

# 列幅
for col_idx in range(1, len(headers) + 1):
    ws.column_dimensions[get_column_letter(col_idx)].width = 15

# 数式
ws['D1'] = '合計'
ws['D2'] = '=SUM(C2:C3)'

# 複数シート
ws2 = wb.create_sheet('グラフ')
ws2['A1'] = 'チャートシート'

wb.save('output.xlsx')
```

### pandasとの連携（大量データ向け）

```python
import pandas as pd

df = pd.DataFrame(data)
with pd.ExcelWriter('output.xlsx', engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='データ', index=False)
    summary.to_excel(writer, sheet_name='サマリ', index=False)
```

### チャート追加

```python
from openpyxl.chart import BarChart, Reference

chart = BarChart()
chart.title = '月次売上'
chart.x_axis.title = '月'
chart.y_axis.title = '売上'

data = Reference(ws, min_col=2, min_row=1, max_col=4, max_row=13)
cats = Reference(ws, min_col=1, min_row=2, max_row=13)
chart.add_data(data, titles_from_data=True)
chart.set_categories(cats)

ws.add_chart(chart, 'F2')
wb.save('output.xlsx')
```

## 日本語フォント対応

- Windows: `Yu Gothic`, `Meiryo`, `MS PGothic`
- macOS: `Hiragino Sans`, `Yu Gothic`
- 生成先環境のフォント可用性を確認してから使う

## よくある落とし穴

- **ファイル上書き**: 既存ファイルは事前にバックアップ、または別ファイル名で出力
- **セル座標**: openpyxlは1-indexed（A1 = row=1, col=1）
- **文字化け**: ExcelがCSVを開く際のエンコーディングは `utf-8-sig` (BOM付き) を推奨
- **巨大ファイル**: 行数10万超は `write_only=True` モードでメモリ削減
- **画像埋め込み**: 相対パスではなく絶対パス推奨

## 推奨ワークフロー

1. **要件確認**: 出力先、フォーマット、読者を明確に
2. **テンプレート有無確認**: 既存テンプレートを編集するほうが見栄えが揃う
3. **最小コード**: 見出し+本文+表の最小構成を先に生成・確認
4. **装飾は最後**: フォント・色・罫線は動作確認後
5. **ファイル検証**: 出力ファイルを実際に開いて表示崩れを確認

## 注意

このスキルは**新規生成・編集**用。既存ファイルから**読み取り・抽出**する場合:
- PDF: Claude Code built-in `Read` tool（pages指定）
- 画像: Read tool（multimodal native）
- Office読取: `scanner` エージェント（MarkItDown MCP経由）
