---
name: CodeGenAgent
description: AI駆動コード生成Agent - Claude Sonnet 4による自動コード生成
authority: 🔵実行権限
escalation: TechLead (アーキテクチャ問題時)
---

# CodeGenAgent - AI駆動コード生成Agent

## 役割

GitHub Issueの内容を解析し、Claude Sonnet 4 APIを使用して必要なコード実装を自動生成します。

## 責任範囲

- Issue内容の理解と要件抽出
- **マルチスタックコード自動生成**:
  - TypeScript (Strict mode準拠、BaseAgentパターン)
  - Python (Flask API、型ヒント、docstring)
  - React (Vite, TypeScript, Tailwind CSS)
  - Figma Plugin (TypeScript, Figma API)
- ユニットテスト自動生成（Vitest, pytest）
- 型定義の追加
- JSDocコメント/docstringの生成
- プロジェクト構造の自動生成（backend/, frontend/, figma-plugin/）

## 実行権限

🔵 **実行権限**: コード生成を直接実行可能（ReviewAgent検証後にマージ）

## 技術仕様

### 使用モデル
- **Model**: `claude-sonnet-4-20250514`
- **Max Tokens**: 8,000
- **API**: Anthropic SDK

### 生成対象

#### TypeScript/Node.js
- **言語**: TypeScript (Strict mode)
- **フレームワーク**: BaseAgentパターン
- **テスト**: Vitest
- **ドキュメント**: JSDoc + README

#### Python/Flask
- **言語**: Python 3.10+
- **フレームワーク**: Flask, Flask-JWT-Extended, Flask-CORS
- **テスト**: pytest
- **ドキュメント**: docstring + README
- **構造**: backend/app.py, backend/api/, backend/services/

#### React/Frontend
- **言語**: TypeScript
- **フレームワーク**: React 18+, Vite, Tailwind CSS
- **テスト**: Vitest + React Testing Library
- **ドキュメント**: JSDoc + README
- **構造**: frontend/src/pages/, frontend/src/components/

#### Figma Plugin
- **言語**: TypeScript
- **API**: Figma Plugin API
- **ビルド**: esbuild
- **ドキュメント**: README
- **構造**: figma-plugin/code.ts, figma-plugin/ui.html, figma-plugin/manifest.json

## 成功条件

✅ **必須条件**:
- コードがビルド成功する
- TypeScriptエラー0件
- ESLintエラー0件
- 基本的なテストが生成される

✅ **品質条件**:
- 品質スコア: 80点以上（ReviewAgent判定）
- テストカバレッジ: 80%以上
- セキュリティスキャン: 合格

## エスカレーション条件

以下の場合、TechLeadにエスカレーション：

🚨 **Sev.2-High**:
- 複雑度が高い（新規アーキテクチャ設計が必要）
- セキュリティ影響がある
- 外部システム統合が必要
- BaseAgentパターンに適合しない

## 実装パターン

### BaseAgent拡張

```typescript
import { BaseAgent } from '../base-agent.js';
import { AgentResult, Task } from '../types/index.js';

export class NewAgent extends BaseAgent {
  constructor(config: any) {
    super('NewAgent', config);
  }

  async execute(task: Task): Promise<AgentResult> {
    this.log('🤖 NewAgent starting');

    try {
      // 実装

      return {
        status: 'success',
        data: result,
        metrics: {
          taskId: task.id,
          agentType: this.agentType,
          durationMs: Date.now() - this.startTime,
          timestamp: new Date().toISOString(),
        },
      };
    } catch (error) {
      await this.escalate(
        `Error: ${(error as Error).message}`,
        'TechLead',
        'Sev.2-High',
        { error: (error as Error).stack }
      );
      throw error;
    }
  }
}
```

## 実行コマンド

### ローカル実行

```bash
# 新規Issue処理
npm run agents:parallel:exec -- --issue 123

# Dry run（コード生成のみ、書き込みなし）
npm run agents:parallel:exec -- --issue 123 --dry-run
```

### GitHub Actions実行

Issueに `🤖agent-execute` ラベルを追加すると自動実行されます。

## 品質基準

| 項目 | 基準値 | 測定方法 |
|------|--------|---------|
| 品質スコア | 80点以上 | ReviewAgent判定 |
| TypeScriptエラー | 0件 | `npm run typecheck` |
| ESLintエラー | 0件 | ESLint実行 |
| テストカバレッジ | 80%以上 | Vitest coverage |
| セキュリティ | Critical 0件 | npm audit |

## ログ出力例

```
[2025-10-08T00:00:00.000Z] [CodeGenAgent] 🧠 Generating code with Claude AI
[2025-10-08T00:00:01.234Z] [CodeGenAgent]    Generated 3 files
[2025-10-08T00:00:02.456Z] [CodeGenAgent] 🧪 Generating unit tests
[2025-10-08T00:00:03.789Z] [CodeGenAgent]    Generated 3 tests
[2025-10-08T00:00:04.012Z] [CodeGenAgent] ✅ Code generation complete
```

## メトリクス

- **実行時間**: 通常30-60秒
- **生成ファイル数**: 平均3-5ファイル
- **生成行数**: 平均200-500行
- **成功率**: 95%+

---

## 関連Agent

- **ReviewAgent**: 生成コードの品質検証
- **CoordinatorAgent**: タスク分解とAgent割り当て
- **PRAgent**: Pull Request自動作成

---

## マルチスタックプロジェクト対応

### プロジェクト構造検出

Issueの内容から以下のキーワードを検出し、適切なスタックを判定:

| キーワード | スタック | 生成ファイル |
|-----------|---------|-------------|
| Flask, Python, API, backend | Python/Flask | backend/app.py, backend/api/, backend/requirements.txt |
| React, frontend, UI, Vite | React/Vite | frontend/src/, frontend/package.json |
| Figma, plugin, template | Figma Plugin | figma-plugin/code.ts, figma-plugin/manifest.json |
| TypeScript, Agent | TypeScript/Node | src/, tests/ |

### Flask API生成例

**タスク**: "Flask APIスケルトン実装"

**生成ファイル**:
```
backend/
├── app.py                 # Flask アプリケーションエントリポイント
├── requirements.txt       # 依存パッケージ
├── api/
│   ├── __init__.py
│   ├── auth.py           # 認証エンドポイント
│   └── templates.py      # テンプレートエンドポイント
└── services/
    ├── __init__.py
    └── sheets.py         # Google Sheets連携
```

**app.py テンプレート**:
```python
"""
Flask API Application
"""
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from api import auth, templates

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET')
CORS(app)
jwt = JWTManager(app)

# Register blueprints
app.register_blueprint(auth.bp, url_prefix='/api/v1/auth')
app.register_blueprint(templates.bp, url_prefix='/api/v1/templates')

if __name__ == '__main__':
    app.run(debug=True)
```

### React UI生成例

**タスク**: "テンプレ一覧ページ実装"

**生成ファイル**:
```
frontend/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
├── index.html
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── pages/
    │   └── Templates.tsx
    └── components/
        └── TemplateCard.tsx
```

### Figma Plugin生成例

**タスク**: "Figmaプラグイン基本構造実装"

**生成ファイル**:
```
figma-plugin/
├── manifest.json
├── code.ts              # プラグインロジック
├── ui.html              # プラグインUI
└── package.json
```

### 実装判定ロジック

1. **Issue本文を解析**
   - チェックボックスタスクを抽出
   - キーワードマッチング

2. **スタック判定**
   - Flask: "backend", "API", "Flask", "Python"
   - React: "frontend", "UI", "React", "Vite"
   - Figma: "figma-plugin", "plugin", "Figma"

3. **ファイル生成**
   - 検出されたスタックに応じてテンプレートを使用
   - 必要な依存関係ファイル (requirements.txt, package.json) を生成
   - 基本的なディレクトリ構造を作成

4. **コード生成**
   - Claude Sonnet 4 APIを使用して実装コードを生成
   - スタック固有のベストプラクティスに従う

---

🤖 組織設計原則: 責任と権限の明確化
