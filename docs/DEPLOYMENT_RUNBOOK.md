# Preview デプロイ & UAT 開始 Runbook

**実施日**: 2025-10-16
**対象コミット**: b114399 (feat: Apply differential updates)
**目的**: 差分コミットをPreview環境へ展開し、UATを開始する

---

## 📋 前提条件チェック

### 必須環境変数

```bash
# Google Cloud
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="asia-northeast1"

# Preview環境URL（デプロイ後に更新）
export API_PREVIEW_BASE="https://tepure-api-preview-xxx.run.app"
export FRONTEND_PREVIEW_URL="https://tepure-preview.web.app"
```

### 必須Secrets（GitHub Secrets / Cloud Run環境変数）

- ✅ `JWT_SECRET`
- ✅ `REFRESH_SECRET`
- ✅ `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64`
- ✅ `FIGMA_API_TOKEN`
- ✅ `LLM_API_KEY` (Anthropic)
- ✅ `SHEETS_USERS_ID`
- ✅ `SHEETS_TEMPLATES_ID`
- ✅ `SHEETS_JOBS_ID`
- ✅ `SHEETS_AUDITLOGS_ID`

### 新規追加Secrets（監視閾値）

- ✅ `ERROR_RATE_THRESHOLD=0.05`
- ✅ `ERROR_RATE_WINDOW_MINUTES=5`
- ✅ `LATENCY_P95_THRESHOLD_MS=2000`
- ✅ `DAILY_COST_THRESHOLD_USD=50.0`

---

## 🔄 Phase 1: バックアップ & マイグレーション

### 1.1 Google Sheets バックアップ（必須）

**手動作業**:
1. Google Sheets を開く
2. 各シートをCSV/Excelでエクスポート:
   - `Users` シート
   - `Templates` シート
   - `Jobs` シート
   - `AuditLogs` シート
3. バックアップを `backups/2025-10-16/` に保存

**CLI（参考）**:
```bash
mkdir -p backups/2025-10-16

# Google Sheets API経由でバックアップ（要実装）
# または手動でExportを推奨
```

### 1.2 マイグレーションスクリプト実行

#### Templates スキーマ拡張

```bash
cd backend

# Python 仮想環境アクティベート
source venv/bin/activate  # macOS/Linux
# または: venv\Scripts\activate  # Windows

# 環境変数読み込み
export $(cat ../.env | grep -v '^#' | xargs)

# マイグレーション実行
python -m app.migrations.20251016_templates_extend

# 実行結果確認（期待: status=completed, updated_rows > 0）
# {
#   "migration": "20251016_templates_extend",
#   "status": "completed",
#   "total_rows": 30,
#   "updated_rows": 30,
#   "new_columns": ["category", "preview_url", "fields", "figma_node_id"],
#   "message": "Migration completed. Please update category, preview_url, fields, and figma_node_id manually."
# }
```

#### Jobs ステータス語彙変換

```bash
# 同じ仮想環境内で
python -m app.migrations.20251016_jobs_status_map

# 実行結果確認（期待: status=completed, updated_rows >= 0）
# {
#   "migration": "20251016_jobs_status_map",
#   "status": "completed",
#   "total_rows": 150,
#   "updated_rows": 120,
#   "errors": [],
#   "error_count": 0
# }
```

#### マイグレーション失敗時のロールバック

```bash
# Templates ロールバック
python -m app.migrations.20251016_templates_extend down

# Jobs ロールバック
python -m app.migrations.20251016_jobs_status_map down
```

### 1.3 手動データ更新（必須）

**マイグレーション後、Google Sheets で以下を手動設定**:

#### Templates シート

| ID | category | preview_url | fields | figma_node_id |
|----|----------|-------------|--------|---------------|
| tpl_001 | LP | https://... | `[{"type":"text","label":"Title","default_value":"Sample"}]` | 1:234 |
| tpl_002 | SNS | https://... | `[{"type":"color","label":"BG","default_value":"#FF5733"}]` | 2:345 |

**fields JSON例**:
```json
[
  {"type": "text", "label": "タイトル", "default_value": "サンプル"},
  {"type": "color", "label": "背景色", "default_value": "#FF5733"},
  {"type": "border", "label": "枠線", "default_value": "solid"}
]
```

---

## 🚀 Phase 2: Preview デプロイ

### 2.1 Backend API デプロイ（Cloud Run）

#### Docker イメージビルド

```bash
cd backend

# Artifact Registry に push
gcloud builds submit \
  --tag asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/tepure/api:preview-20251016 \
  --tag asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/tepure/api:preview

# ビルド完了確認
gcloud builds list --limit=1
```

#### Cloud Run デプロイ

```bash
gcloud run deploy tepure-api-preview \
  --image asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/tepure/api:preview-20251016 \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 5 \
  --min-instances 0 \
  --timeout 60 \
  --set-env-vars "\
ENV=preview,\
APP_VERSION=1.0.0-preview,\
ERROR_RATE_THRESHOLD=0.05,\
ERROR_RATE_WINDOW_MINUTES=5,\
LATENCY_P95_THRESHOLD_MS=2000,\
DAILY_COST_THRESHOLD_USD=50.0" \
  --set-secrets "\
JWT_SECRET=jwt-secret:latest,\
REFRESH_SECRET=refresh-secret:latest,\
GOOGLE_SERVICE_ACCOUNT_JSON_BASE64=google-sa-json:latest,\
FIGMA_API_TOKEN=figma-token:latest,\
LLM_API_KEY=anthropic-key:latest,\
SHEETS_USERS_ID=sheets-users-id:latest,\
SHEETS_TEMPLATES_ID=sheets-templates-id:latest,\
SHEETS_JOBS_ID=sheets-jobs-id:latest,\
SHEETS_AUDITLOGS_ID=sheets-auditlogs-id:latest"

# デプロイ成功確認
gcloud run services describe tepure-api-preview \
  --region asia-northeast1 \
  --format 'value(status.url)'

# URL を環境変数に保存
export API_PREVIEW_BASE=$(gcloud run services describe tepure-api-preview \
  --region asia-northeast1 \
  --format 'value(status.url)')
```

### 2.2 Frontend デプロイ（Firebase Hosting）

#### ビルド & デプロイ

```bash
cd frontend

# 依存関係インストール
npm ci

# 環境変数設定（Preview API URL）
echo "VITE_API_BASE=$API_PREVIEW_BASE" > .env.preview

# ビルド
npm run build

# Firebase Preview Channel にデプロイ（7日間有効）
firebase hosting:channel:deploy preview-20251016 \
  --expires 7d

# Preview URL 取得
export FRONTEND_PREVIEW_URL=$(firebase hosting:channel:open preview-20251016 --json | jq -r '.url')

echo "Frontend Preview URL: $FRONTEND_PREVIEW_URL"
```

---

## 🧪 Phase 3: スモークテスト

### 3.1 Health Check

```bash
# /health エンドポイント確認
curl -s ${API_PREVIEW_BASE}/health | jq .

# 期待レスポンス:
# {
#   "ok": true,
#   "version": "1.0.0-preview",
#   "git": "b114399"
# }
```

### 3.2 認証テスト

```bash
# ログイン
JWT=$(curl -s -X POST "$API_PREVIEW_BASE/api/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@example.com","password":"password123"}' \
  | jq -r '.access_token')

# トークン確認
echo "JWT Token: ${JWT:0:20}..."

# 期待: JWT token が返却される
```

### 3.3 Templates API テスト

```bash
# Templates 一覧取得
curl -s -H "Authorization: Bearer $JWT" \
  "$API_PREVIEW_BASE/api/v1/templates?category=LP&size=5" \
  | jq '{count: .templates|length, total: .total, first_template: .templates[0]}'

# 期待:
# - templates 配列が存在
# - category フィルターが動作
# - 各テンプレートに category, fields, preview_url が含まれる
```

### 3.4 Jobs API テスト

```bash
# Job 作成
JOB_RESPONSE=$(curl -s -X POST "$API_PREVIEW_BASE/api/v1/templates/tpl_001/use" \
  -H "Authorization: Bearer $JWT" \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: smoke-test-20251016-001' \
  -d '{
    "template_id": "tpl_001",
    "inputs": {"title": "SMOKE TEST"},
    "temperature": 0.7,
    "intensity": "medium",
    "idempotency_key": "smoke-test-20251016-001"
  }')

JOB_ID=$(echo $JOB_RESPONSE | jq -r '.job_id')

echo "Job ID: $JOB_ID"
echo "Initial Status: $(echo $JOB_RESPONSE | jq -r '.status')"

# 期待: status が "pending"

# Job ステータス確認
sleep 5

curl -s -H "Authorization: Bearer $JWT" \
  "$API_PREVIEW_BASE/api/v1/jobs/$JOB_ID" \
  | jq '{job_id, status, usage}'

# 期待:
# - status が "processing" または "completed"
# - usage.total_tokens <= 1500
```

### 3.5 Idempotency テスト

```bash
# 同じ Idempotency-Key で再実行
JOB_RESPONSE_2=$(curl -s -X POST "$API_PREVIEW_BASE/api/v1/templates/tpl_001/use" \
  -H "Authorization: Bearer $JWT" \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: smoke-test-20251016-001' \
  -d '{
    "template_id": "tpl_001",
    "inputs": {"title": "SMOKE TEST"},
    "temperature": 0.7,
    "intensity": "medium",
    "idempotency_key": "smoke-test-20251016-001"
  }')

JOB_ID_2=$(echo $JOB_RESPONSE_2 | jq -r '.job_id')

# 期待: JOB_ID == JOB_ID_2（重複作成されない）
echo "Original Job ID: $JOB_ID"
echo "Duplicate Job ID: $JOB_ID_2"
```

### 3.6 エラーハンドリングテスト

#### 422 Token Budget Exceeded

```bash
# 大量入力でトークン超過を意図的に発生
curl -s -X POST "$API_PREVIEW_BASE/api/v1/templates/tpl_001/use" \
  -H "Authorization: Bearer $JWT" \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: smoke-test-token-exceeded' \
  -d '{
    "template_id": "tpl_001",
    "inputs": {"title": "'"$(python3 -c "print('A'*10000)")"'"},
    "temperature": 1.0,
    "intensity": "high",
    "idempotency_key": "smoke-test-token-exceeded"
  }' | jq .

# 期待:
# {
#   "code": "TOKEN_BUDGET_EXCEEDED",
#   "message": "Agent1 token limit exceeded: ...",
#   "details": {...}
# }
```

#### 429 Rate Limit

```bash
# 連続リクエストでレート制限発動
for i in {1..10}; do
  curl -s -X POST "$API_PREVIEW_BASE/api/v1/templates/tpl_001/use" \
    -H "Authorization: Bearer $JWT" \
    -H 'Content-Type: application/json' \
    -H "Idempotency-Key: smoke-test-ratelimit-$i" \
    -d '{
      "template_id": "tpl_001",
      "inputs": {"title": "Rate Test '$i'"},
      "temperature": 0.7,
      "intensity": "low",
      "idempotency_key": "smoke-test-ratelimit-'$i'"
    }' &
done

wait

# 期待: 一部が 429 Too Many Requests を返す
```

---

## 📊 Phase 4: UAT 準備

### 4.1 テスターアカウント作成

```bash
# テスター用アカウントリスト
TESTERS=(
  "tester1@example.com:password123:user"
  "tester2@example.com:password123:user"
  "tester3@example.com:password123:user"
  "tester_admin@example.com:admin123:admin"
)

# Google Sheets Users シートに手動追加
# または API 経由で作成（実装次第）
```

**Users シート 追加例**:

| id | email | password_hash | role | monthly_quota | created_at |
|----|-------|---------------|------|---------------|------------|
| usr_uat_001 | tester1@example.com | $2b$12$... | user | 50 | 2025-10-16T00:00:00Z |
| usr_uat_002 | tester2@example.com | $2b$12$... | user | 50 | 2025-10-16T00:00:00Z |
| usr_uat_003 | tester3@example.com | $2b$12$... | user | 50 | 2025-10-16T00:00:00Z |
| usr_uat_admin | tester_admin@example.com | $2b$12$... | admin | 200 | 2025-10-16T00:00:00Z |

### 4.2 UAT 告知作成

**メール/Slackテンプレート**:

```
件名: 【UAT開始】tepure Preview環境テスト実施のお願い

皆様

お疲れ様です。tepure（Figmaテンプレート自動化システム）のPreview環境が準備完了しました。
本日よりUATを開始しますので、ご協力をお願いいたします。

■ UAT期間
2025-10-16（水）〜 2025-10-18（金）17:00

■ Preview環境URL
- Frontend: ${FRONTEND_PREVIEW_URL}
- API: ${API_PREVIEW_BASE}

■ テスターアカウント
Email: （個別に配布）
Password: （個別に配布）

■ テスト項目
docs/UAT_CHECKLIST.md を参照
重点確認:
- Templates一覧でcategoryフィルター動作
- Template詳細でfields配列表示
- Job作成後、status遷移（pending→processing→completed）
- /health エンドポイント正常レスポンス

■ 不具合報告
GitHub Issues: https://github.com/your-org/tepure/issues
ラベル: uat, P0/P1/P2
スクリーンショット/動画を添付してください

■ 緊急連絡先
Email: owner@example.com
Slack: #tepure-uat

よろしくお願いいたします。
```

### 4.3 UAT チェックリスト配布

```bash
# UAT チェックリストをPDF化（オプション）
cd docs
pandoc UAT_CHECKLIST.md -o UAT_CHECKLIST.pdf

# テスターに配布
# - GitHub 経由
# - Slack/Email 添付
```

---

## ✅ Phase 5: 受け入れチェックリスト

### スモーク & データ移行

- [ ] Google Sheets 4表を事前バックアップ完了
- [ ] `20251016_templates_extend` 実行ログOK（status=completed）
- [ ] `20251016_jobs_status_map` 実行ログOK（status=completed）
- [ ] `/health` が `{ ok: true, version, git }` を返す

### API/機能

- [ ] `GET /api/v1/templates` の配列キーが `templates`
- [ ] `POST /use` → `GET /jobs/{id}` で `completed` まで到達
- [ ] Idempotency-Key 重複で再実行されない
- [ ] 422 Token Budget Exceeded エラーが適切に返却

### 監視/コスト

- [ ] `ERROR_RATE_THRESHOLD=0.05` / `P95=2000ms` / `DAILY_COST=$50` がENVに設定
- [ ] 1ジョブあたり `tokens <= 1500` を確認（usageログ/レスポンス）

### UAT準備

- [ ] テスター3〜5名にアカウント配布（userロール）
- [ ] UAT告知（URL・期間・報告フォーム）を送信
- [ ] 重大Issue（P0）時の連絡線を共有

---

## 🔧 トラブルシューティング

### Cloud Run デプロイ失敗

**症状**: `gcloud run deploy` が失敗

**原因**:
- Artifact Registry にイメージが存在しない
- Secrets が未設定

**対処**:
```bash
# イメージ存在確認
gcloud artifacts docker images list \
  asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/tepure

# Secrets 存在確認
gcloud secrets list | grep -E 'jwt-secret|anthropic-key'
```

### マイグレーションエラー

**症状**: `python -m app.migrations.xxx` がエラー

**原因**:
- Google Sheets API レート制限
- 環境変数未設定

**対処**:
```bash
# レート制限回避: リトライ間隔を増やす
# または手動でシート更新

# 環境変数確認
env | grep -E 'SHEETS_|GOOGLE_'
```

### Frontend ビルドエラー

**症状**: `npm run build` が失敗

**原因**:
- Node.js バージョン不一致
- 依存関係の不整合

**対処**:
```bash
# Node.js バージョン確認
node -v  # 期待: v20.x

# クリーンインストール
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

## 📚 参考ドキュメント

- **マイグレーションガイド**: `docs/MIGRATION_GUIDE.md`
- **差分実装サマリー**: `docs/DIFFERENTIAL_UPDATE_SUMMARY.md`
- **UAT チェックリスト**: `docs/UAT_CHECKLIST.md`
- **アーキテクチャ**: `docs/ARCHITECTURE.md`

---

## 📝 実施ログ

| タイムスタンプ | フェーズ | ステータス | 備考 |
|--------------|---------|----------|------|
| 2025-10-16 09:00 | Phase 1 | 開始 | バックアップ取得開始 |
| 2025-10-16 09:15 | Phase 1 | 完了 | マイグレーション成功 |
| 2025-10-16 10:00 | Phase 2 | 完了 | Preview デプロイ完了 |
| 2025-10-16 10:30 | Phase 3 | 完了 | スモークテスト全パス |
| 2025-10-16 11:00 | Phase 4 | 完了 | UAT告知送信 |

---

**実施者**: オーナー
**監視者**: オーナー
**承認者**: プロジェクトオーナー

---

🚀 **Preview デプロイ完了後、UAT を開始してください。**
