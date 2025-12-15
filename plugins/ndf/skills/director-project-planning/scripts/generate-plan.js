#!/usr/bin/env node

/**
 * プロジェクト計画書生成スクリプト
 *
 * 対話的にユーザーからプロジェクト情報を収集し、
 * テンプレートを使用して構造化された計画書を生成します。
 *
 * 使用方法:
 *   node generate-plan.js
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

// 対話インターフェースの設定
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

/**
 * ユーザーに質問して回答を取得
 */
function question(prompt) {
  return new Promise((resolve) => {
    rl.question(prompt, (answer) => {
      resolve(answer);
    });
  });
}

/**
 * テンプレートファイルを読み込む
 */
function loadTemplate(templateName) {
  const templatePath = path.join(__dirname, '..', 'templates', templateName);
  try {
    return fs.readFileSync(templatePath, 'utf-8');
  } catch (error) {
    console.error(`エラー: テンプレート ${templateName} が見つかりません`);
    process.exit(1);
  }
}

/**
 * タスクをフェーズに分解
 */
function generateTaskBreakdown(projectInfo) {
  const phases = [
    {
      name: 'フェーズ1: 調査・要件定義',
      agent: 'researcher',
      duration: '1-2日',
      tasks: [
        '既存コードベースの調査（Serena MCPで構造理解）',
        '外部ドキュメント・ベストプラクティスの調査',
        '技術選定（ライブラリ、フレームワーク）',
        '要件定義書作成'
      ]
    },
    {
      name: 'フェーズ2: 設計',
      agent: 'data-analyst, corder',
      duration: '2-3日',
      tasks: [
        'データベーススキーマ設計',
        'API設計（エンドポイント、リクエスト/レスポンス）',
        'アーキテクチャ設計（モジュール構成、依存関係）'
      ]
    },
    {
      name: 'フェーズ3: 実装',
      agent: 'corder',
      duration: '3-5日',
      tasks: [
        'バックエンド実装（データベースモデル、APIエンドポイント、ビジネスロジック）',
        'フロントエンド実装（UIコンポーネント、API連携、状態管理）'
      ],
      parallelizable: 'バックエンドとフロントエンドは並列実装可能'
    },
    {
      name: 'フェーズ4: テスト',
      agent: 'qa, corder',
      duration: '2-3日',
      tasks: [
        '単体テスト作成・実行',
        '統合テスト作成・実行',
        'コードレビュー（品質・セキュリティ）',
        'セキュリティスキャン'
      ],
      parallelizable: '単体テストとセキュリティスキャンは並列実行可能'
    },
    {
      name: 'フェーズ5: ドキュメント・デプロイ',
      agent: 'corder',
      duration: '1-2日',
      tasks: [
        'API仕様書作成',
        'README更新',
        'インラインコメント追加'
      ]
    }
  ];

  return phases;
}

/**
 * リスクを識別
 */
function identifyRisks(projectInfo) {
  const commonRisks = [
    {
      name: '既存機能の破壊',
      probability: '中',
      impact: '高',
      mitigation: 'テストカバレッジ80%以上を確保、段階的なリリース'
    },
    {
      name: '技術的負債の増加',
      probability: '中',
      impact: '中',
      mitigation: 'コードレビューの徹底、リファクタリング時間の確保'
    },
    {
      name: 'セキュリティ脆弱性',
      probability: '低',
      impact: '高',
      mitigation: 'Codex CLI MCPでセキュリティスキャン実施、OWASP Top 10の遵守'
    }
  ];

  return commonRisks;
}

/**
 * 計画書を生成
 */
function generatePlan(projectInfo, phases, risks) {
  let template = loadTemplate('project-plan-template.md');

  // 基本情報を置換
  const today = new Date().toISOString().split('T')[0];
  template = template.replace(/\[プロジェクト名\]/g, projectInfo.name);
  template = template.replace(/\[YYYY-MM-DD\]/g, today);

  // 概要セクションを置換
  template = template.replace(/\[このプロジェクトの目的を明確に記述\]/g, projectInfo.purpose);

  // スコープを置換
  const scopeInItems = projectInfo.scope.split(',').map(s => `- ${s.trim()}`).join('\n');
  template = template.replace(/- \[実装する機能1\]\n- \[実装する機能2\]\n- \[実装する機能3\]/, scopeInItems);

  // 期限を置換（提供されていれば）
  if (projectInfo.deadline) {
    template = template.replace(/\*\*終了予定日\*\*: \[YYYY-MM-DD\]/, `**終了予定日**: ${projectInfo.deadline}`);
  }

  // 受入基準を置換（提供されていれば）
  if (projectInfo.acceptanceCriteria) {
    const criteriaItems = projectInfo.acceptanceCriteria.split(',').map(c => `- [ ] ${c.trim()}`).join('\n');
    template = template.replace(/- \[ \] \[成果物1\]\n- \[ \] \[成果物2\]\n- \[ \] \[成果物3\]/, criteriaItems);
  }

  return template;
}

/**
 * 計画書をファイルに保存
 */
function savePlan(projectInfo, content) {
  // 保存先ディレクトリを決定（issuesディレクトリまたはカレントディレクトリ）
  const possibleDirs = [
    path.join(process.cwd(), 'issues'),
    process.cwd()
  ];

  let saveDir = possibleDirs.find(dir => {
    try {
      return fs.existsSync(dir);
    } catch (e) {
      return false;
    }
  });

  if (!saveDir) {
    // issuesディレクトリを作成
    saveDir = possibleDirs[0];
    fs.mkdirSync(saveDir, { recursive: true });
  }

  // ファイル名を生成（プロジェクト名をケバブケースに変換）
  const kebabName = projectInfo.name
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9-]/g, '');
  const filename = `${kebabName}-plan.md`;
  const filepath = path.join(saveDir, filename);

  // ファイルに保存
  fs.writeFileSync(filepath, content, 'utf-8');
  console.log(`\n✅ 計画書を保存しました: ${filepath}`);

  return filepath;
}

/**
 * メイン処理
 */
async function main() {
  console.log('=== プロジェクト計画書生成ツール ===\n');
  console.log('プロジェクト情報を入力してください。\n');

  // プロジェクト情報を収集
  const projectInfo = {
    name: await question('プロジェクト名: '),
    purpose: await question('目的（このプロジェクトで達成したいこと）: '),
    scope: await question('スコープ（実装する機能をカンマ区切りで）: '),
    deadline: await question('期限（YYYY-MM-DD形式、任意）: '),
    acceptanceCriteria: await question('受入基準（カンマ区切りで、任意）: ')
  };

  console.log('\n計画書を生成中...\n');

  // タスク分解を生成
  const phases = generateTaskBreakdown(projectInfo);
  console.log(`✅ ${phases.length}個のフェーズに分解しました`);

  // リスクを識別
  const risks = identifyRisks(projectInfo);
  console.log(`✅ ${risks.length}個のリスクを識別しました`);

  // 計画書を生成
  const plan = generatePlan(projectInfo, phases, risks);

  // 計画書を保存
  const filepath = savePlan(projectInfo, plan);

  console.log('\n=== 計画書の概要 ===');
  console.log(`プロジェクト名: ${projectInfo.name}`);
  console.log(`フェーズ数: ${phases.length}`);
  console.log(`識別されたリスク数: ${risks.length}`);
  console.log('\n次のステップ:');
  console.log('1. 生成された計画書を確認・調整してください');
  console.log('2. 必要に応じてタスク分解テンプレートを使用して詳細化してください');
  console.log('3. リスク評価テンプレートでリスクを詳細に評価してください');
  console.log('4. 計画に基づいて実装を開始してください\n');

  rl.close();
}

// エントリーポイント
main().catch((error) => {
  console.error('エラーが発生しました:', error);
  rl.close();
  process.exit(1);
});
