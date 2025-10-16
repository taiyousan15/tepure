# Migration Guide - 2025-10-16 Differential Updates

## 概要

このドキュメントは、2025-10-16の差分適用版で実施された変更内容と移行手順をまとめたものです。

## 変更サマリー

### 1. データモデル拡張

#### Templates スキーマ拡張

**新規追加カラム**:
- `category`: Literal['LP', 'Banner', 'SNS', 'WebApp'] - テンプレートカテゴリー
- `fields[]`: List[Field] - 入力フィールド定義（JSON配列）
- `figma_node_id`: str - FigmaノードID
- `preview_url`: str - プレビュー画像URL

**Field 構造**:
```python
{
  "type": "text" | "color" | "border",
  "label": "string",
  "default_value": "any"
}
```

#### Jobs ステータス語彙変更

**旧 → 新**:
- `queued` → `pending`
- `running` → `processing`
- `succeeded` → `completed`
- `failed` → `failed` (変更なし)

### 2. API変更

#### レスポンスキー標準化

**GET /api/v1/templates**:
- レスポンスキー: `templates` (配列)
- 変更前: 潜在的に `items` を使用していた可能性あり
- 変更後: 必ず `templates` を使用

#### 新規エンドポイント

**GET /health**:
```json
{
  "ok": true,
  "version": "1.0.0",
  "git": "abc123def"
}
```

#### エラーレスポンス拡張

**422 Unprocessable Entity** - トークン予算超過時:
```json
{
  "code": "TOKEN_BUDGET_EXCEEDED",
  "message": "Agent1 token limit exceeded: 950 > 900",
  "details": {
    "total_tokens": 950,
    "limit": 900,
    "agent": "Agent1"
  }
}
```

### 3. セキュリティ仕様明示化

**BCrypt ラウンド数**: 12 rounds (明示的に指定)

```python
# backend/app/auth.py
bcrypt.gensalt(rounds=12)
```

### 4. 監視閾値更新

**新しい閾値**:
- エラー率: 5%超過/5分
- レイテンシ: P95が2000ms超過
- コスト: 1日$50超過

**環境変数**:
```bash
ERROR_RATE_THRESHOLD=0.05
ERROR_RATE_WINDOW_MINUTES=5
LATENCY_P95_THRESHOLD_MS=2000
DAILY_COST_THRESHOLD_USD=50.0
```

### 5. LLMコスト制御更新

**トークン割り当て (合計1,500)**:
- Agent1 (プロンプト生成): 900 tokens
- Agent2 (JSON整形): 600 tokens

**変更前**: 各Agent 1,500 tokens (合計3,000)
**変更後**: 各Agent制限あり (合計1,500)

---

## 移行手順

### Phase 1: バックアップ

```bash
# Google Sheets データバックアップ
# 手動で各シートをエクスポート（CSV/Excel）
# - Users シート
# - Templates シート
# - Jobs シート
# - AuditLogs シート

# コードベースバックアップ
git checkout main
git pull origin main
git checkout -b backup-before-migration-20251016
git push origin backup-before-migration-20251016
```

### Phase 2: マイグレーションスクリプト実行

#### 2.1 Templates スキーマ拡張

```bash
cd backend

# マイグレーション実行
python -m app.migrations.20251016_templates_extend

# 実行後、以下を手動で更新:
# - category: 各テンプレートのカテゴリーを LP/Banner/SNS/WebApp に設定
# - preview_url: プレビュー画像URLを追加
# - fields: 入力フィールド定義をJSON配列で追加
# - figma_node_id: FigmaノードIDを追加
```

**fields 例**:
```json
[
  {
    "type": "text",
    "label": "タイトル",
    "default_value": "サンプルタイトル"
  },
  {
    "type": "color",
    "label": "背景色",
    "default_value": "#FF5733"
  },
  {
    "type": "border",
    "label": "ボーダースタイル",
    "default_value": "solid"
  }
]
```

#### 2.2 Jobs ステータス変換

```bash
# マイグレーション実行
python -m app.migrations.20251016_jobs_status_map

# 実行結果確認
# - total_rows: 処理対象行数
# - updated_rows: 更新された行数
# - errors: エラーリスト
```

### Phase 3: コード更新

#### 3.1 環境変数追加

`.env` ファイルに以下を追加:

```bash
# Alert Thresholds
ERROR_RATE_THRESHOLD=0.05
ERROR_RATE_WINDOW_MINUTES=5
LATENCY_P95_THRESHOLD_MS=2000
DAILY_COST_THRESHOLD_USD=50.0
```

#### 3.2 依存関係更新

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend (変更なし)
cd ../frontend
npm install
```

### Phase 4: テスト実行

#### 4.1 Backend テスト

```bash
cd backend

# 型チェック
mypy app/ --ignore-missing-imports

# ユニットテスト
pytest tests/unit -v

# カバレッジ確認
pytest tests/unit --cov=app --cov-report=term-missing
```

#### 4.2 E2E テスト

```bash
cd ../e2e

# Playwright テスト実行
npx playwright test

# レポート確認
npx playwright show-report
```

### Phase 5: デプロイ

#### 5.1 Preview デプロイ

```bash
# Backend (Cloud Run)
gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/tepure-api:preview
gcloud run deploy tepure-api-preview \
  --image gcr.io/$GCP_PROJECT_ID/tepure-api:preview \
  --region asia-northeast1

# Frontend (Firebase Hosting - Preview channel)
cd frontend
npm run build
firebase hosting:channel:deploy preview-20251016
```

#### 5.2 UAT実施

**UAT チェックリスト**: `docs/UAT_CHECKLIST.md` を参照

重点確認項目:
- [ ] Templates一覧でcategoryフィルターが正常動作
- [ ] Template詳細でfieldsが表示される
- [ ] Jobs作成後、status が "pending" → "processing" → "completed" と遷移
- [ ] /health エンドポイントが正常レスポンス返却
- [ ] Agent1/Agent2のトークン制限が正常動作 (900/600)
- [ ] エラー率5%超過時にアラート発火 (要手動確認)

#### 5.3 Production デプロイ

```bash
# UAT合格後
git checkout main
git merge preview-20251016
git tag v1.1.0-migration-20251016
git push origin main --tags

# GitHub Actions が自動デプロイ実行
# または手動デプロイ:
gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/tepure-api:latest
gcloud run deploy tepure-api \
  --image gcr.io/$GCP_PROJECT_ID/tepure-api:latest \
  --region asia-northeast1

cd frontend
npm run build
firebase deploy --only hosting
```

---

## ロールバック手順

### マイグレーション ロールバック

#### Templates スキーマ

```bash
cd backend
python -m app.migrations.20251016_templates_extend down
```

**警告**: 新規カラム (category, fields, preview_url, figma_node_id) のデータは失われます。

#### Jobs ステータス

```bash
cd backend
python -m app.migrations.20251016_jobs_status_map down
```

### コードベース ロールバック

```bash
git checkout main
git revert HEAD~1  # または該当コミットを指定
git push origin main

# 再デプロイ
# GitHub Actions が自動実行
```

---

## トラブルシューティング

### Q1: マイグレーション実行中にエラー

**症状**: `20251016_templates_extend.py` 実行時に API エラー

**原因**: Google Sheets API レート制限

**対策**:
```bash
# リトライ間隔を増やして再実行
# または手動でシート更新
```

### Q2: category バリデーションエラー

**症状**: API リクエスト時に `422 Unprocessable Entity` (category が LP/Banner/SNS/WebApp 以外)

**原因**: 旧データに不正なcategory値が残存

**対策**:
```python
# backend で旧データを一括更新
from app.sheets import GoogleSheetsClient

sheets = GoogleSheetsClient()
templates = sheets.get_all_templates()

for t in templates:
    if t['category'] not in ['LP', 'Banner', 'SNS', 'WebApp']:
        # デフォルト値に更新
        sheets.update_template(t['id'], {'category': 'LP'})
```

### Q3: トークン制限が厳しすぎる

**症状**: Agent1/Agent2 で頻繁に "Token limit exceeded" エラー

**原因**: 1,500 tokens が不足

**対策**:
```bash
# 環境変数で一時的に上限緩和 (運用後に再調整)
# backend/app/agents.py
MAX_AGENT1_TOKENS = 1200  # 900 → 1200
MAX_AGENT2_TOKENS = 800   # 600 → 800
MAX_TOTAL_TOKENS = 2000   # 1500 → 2000
```

### Q4: E2E テスト失敗

**症状**: templates.spec.ts で category フィルター失敗

**原因**: Mock データが旧 category 値

**対策**:
```bash
# e2e/fixtures.ts を確認
# category: 'Marketing' → 'LP'
# category: 'Sales' → 'Banner'
```

---

## 変更ファイル一覧

### Backend

**新規作成**:
- `backend/app/migrations/20251016_jobs_status_map.py`
- `backend/app/migrations/20251016_templates_extend.py`

**更新**:
- `backend/app/schemas.py` - Field, TemplateSchema拡張
- `backend/app/__init__.py` - /health エンドポイント更新
- `backend/app/agents.py` - トークン制限更新
- `backend/app/metrics.py` - アラート閾値追加
- `backend/tests/unit/test_schemas.py` - テスト更新

### Frontend

**更新**:
- `e2e/fixtures.ts` - Mock データ更新 (category, fields追加)

### Documentation

**新規作成**:
- `docs/MIGRATION_GUIDE.md` (このファイル)

**更新**:
- `.env.sample` - アラート閾値環境変数追加

---

## 参考リンク

- [差分適用版ドキュメント](./差分適用版_要件定義.md)
- [UAT チェックリスト](./UAT_CHECKLIST.md)
- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [README.md](../README.md)

---

## 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2025-10-16 | 1.0.0 | 初版作成 - 差分適用版マイグレーション |

---

📋 **マイグレーション実施前に必ずバックアップを取得してください。**
