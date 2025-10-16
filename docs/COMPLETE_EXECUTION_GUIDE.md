# 完全実行ガイド - Preview デプロイ→UAT開始

**実施日**: 2025-10-16
**所要時間**: 約60-90分
**前提**: GCP/Firebase権限、gcloud/firebase-tools/jq/python3インストール済み

---

## 📋 実行前チェックリスト

### 必須ツール確認

```bash
# すべて OK が表示されることを確認
gcloud --version  # OK: Google Cloud SDK xxx
firebase --version  # OK: xxx
jq --version  # OK: jq-1.x
python3 --version  # OK: Python 3.11+
```

### 環境変数設定

```bash
# プロジェクトID設定
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="asia-northeast1"

# 確認
echo "Project: $GCP_PROJECT_ID"
echo "Region: $GCP_REGION"
```

---

## 🚀 Phase 1: Secrets Preflight（5分）

### 1.1 ローカル .env ファイル確認

```bash
# .env ファイルが存在することを確認
ls -la .env

# Secrets チェック実行
python3 ops/check-secrets.py --source file --file .env --json

# 期待出力: {"ok": true, ...}
```

**❌ NG の場合**:
```bash
# 不足しているキーを確認
python3 ops/check-secrets.py --source file --file .env

# 出力例:
# ❌ Missing required keys (2):
#    - JWT_SECRET
#    - LLM_API_KEY
```

**対処**: `.env` に不足キーを追加し、再度チェック

```bash
# .env に追加
echo "JWT_SECRET=your-secret-here" >> .env
echo "LLM_API_KEY=your-key-here" >> .env

# 再チェック
python3 ops/check-secrets.py --source file --file .env --json
```

### 1.2 GitHub Secrets 確認（CI用）

```bash
# GitHub Secrets が設定されているか確認（GUIで実施）
# Settings → Secrets and variables → Actions

# 必須:
# - JWT_SECRET
# - REFRESH_SECRET
# - GOOGLE_SERVICE_ACCOUNT_JSON_BASE64
# - FIGMA_API_TOKEN
# - LLM_API_KEY
# - SHEETS_USERS_ID
# - SHEETS_TEMPLATES_ID
# - SHEETS_JOBS_ID
# - SHEETS_AUDITLOGS_ID
# - SENTRY_DSN
# - GA_MEASUREMENT_ID
```

---

## 💾 Phase 2: バックアップ（10分）

### 2.1 Google Sheets バックアップ

**手動作業（GUI）**:

1. Google Sheets を開く
2. 各シートをエクスポート:
   ```
   Users シート → ファイル → ダウンロード → CSV
   Templates シート → ファイル → ダウンロード → CSV
   Jobs シート → ファイル → ダウンロード → CSV
   AuditLogs シート → ファイル → ダウンロード → CSV
   ```

3. ローカルに保存:
   ```bash
   mkdir -p backups/2025-10-16
   # ダウンロードしたCSVをこのフォルダに移動
   ```

4. バックアップ確認:
   ```bash
   ls -lh backups/2025-10-16/
   # 期待: 4つのCSVファイル
   ```

---

## 🔄 Phase 3: マイグレーション実行（15分）

### 3.1 Python 仮想環境準備

```bash
cd backend

# 仮想環境アクティベート
source venv/bin/activate  # macOS/Linux
# または: venv\Scripts\activate  # Windows

# 環境変数読み込み
export $(cat ../.env | grep -v '^#' | xargs)

# Python バージョン確認
python --version  # 期待: Python 3.11+
```

### 3.2 Templates スキーマ拡張

```bash
# マイグレーション実行
python -m app.migrations.20251016_templates_extend

# 成功時の出力例:
# {
#   "migration": "20251016_templates_extend",
#   "status": "completed",
#   "total_rows": 30,
#   "updated_rows": 30,
#   "new_columns": ["category", "preview_url", "fields", "figma_node_id"],
#   "message": "Migration completed. Please update category, preview_url, fields, and figma_node_id manually."
# }
```

**✅ 成功確認**:
- `"status": "completed"`
- `"updated_rows" > 0`

**❌ 失敗時のロールバック**:
```bash
python -m app.migrations.20251016_templates_extend down
# バックアップから復元（最終手段）
```

### 3.3 Jobs ステータス語彙変換

```bash
# マイグレーション実行
python -m app.migrations.20251016_jobs_status_map

# 成功時の出力例:
# {
#   "migration": "20251016_jobs_status_map",
#   "status": "completed",
#   "total_rows": 150,
#   "updated_rows": 120,
#   "errors": [],
#   "error_count": 0
# }
```

**✅ 成功確認**:
- `"status": "completed"`
- `"error_count": 0`

**❌ 失敗時のロールバック**:
```bash
python -m app.migrations.20251016_jobs_status_map down
```

### 3.4 手動データ更新（推奨）

**Google Sheets で以下を手動設定**:

#### Templates シート

| カラム | 値 | 例 |
|-------|---|---|
| category | LP/Banner/SNS/WebApp | LP |
| fields | JSON配列 | `[{"type":"text","label":"Title","default_value":"Sample"}]` |
| preview_url | 画像URL | `https://example.com/thumb.png` |
| figma_node_id | ノードID | `1:234` |

**最低限**:
- 主要テンプレート（3-5個）に `category` と `fields` を設定

---

## 🏗️ Phase 4: Preview デプロイ（20分）

### 4.1 Backend API デプロイ（Cloud Run）

```bash
cd backend

# Docker イメージビルド＆プッシュ
gcloud builds submit \
  --tag asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/tepure/api:preview-20251016 \
  --project $GCP_PROJECT_ID

# ビルド確認
gcloud builds list --project $GCP_PROJECT_ID --limit=1

# ✅ 成功: STATUS=SUCCESS
```

**Cloud Run デプロイ**:

```bash
# GIT_SHA取得
GIT_SHA=$(git rev-parse --short HEAD)

# デプロイ実行
gcloud run deploy tepure-api-preview \
  --image asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/tepure/api:preview-20251016 \
  --region $GCP_REGION \
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
GIT_COMMIT=$GIT_SHA,\
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
SHEETS_AUDITLOGS_ID=sheets-auditlogs-id:latest" \
  --project $GCP_PROJECT_ID

# デプロイ成功確認
gcloud run services describe tepure-api-preview \
  --region $GCP_REGION \
  --project $GCP_PROJECT_ID \
  --format 'value(status.url)'

# ✅ 成功: URL が表示される
```

**URL を環境変数に保存**:

```bash
export API_PREVIEW_BASE=$(gcloud run services describe tepure-api-preview \
  --region $GCP_REGION \
  --project $GCP_PROJECT_ID \
  --format 'value(status.url)')

echo "API Preview URL: $API_PREVIEW_BASE"
# 表示例: https://tepure-api-preview-xxx.run.app
```

### 4.2 Frontend デプロイ（Firebase Hosting）

```bash
cd frontend

# 依存関係インストール
npm ci

# 環境変数設定（Preview API URL）
echo "VITE_API_BASE=$API_PREVIEW_BASE" > .env.preview

# ビルド
npm run build

# ビルド確認
ls -lh dist/
# ✅ 成功: dist/ にファイルが生成される

# Firebase Preview Channel にデプロイ（7日間有効）
firebase hosting:channel:deploy preview-20251016 \
  --expires 7d

# ✅ 成功: Preview URL が表示される
```

**URL を環境変数に保存**:

```bash
# Firebase CLI の出力から URL をコピー
export FRONTEND_PREVIEW_URL="https://tepure---preview-20251016-xxx.web.app"

echo "Frontend Preview URL: $FRONTEND_PREVIEW_URL"
```

---

## 🧪 Phase 5: スモークテスト（15分）

### 5.1 自動スモークテスト実行

```bash
cd ..  # プロジェクトルートへ

# スモークテスト実行
./scripts/smoke-test.sh $API_PREVIEW_BASE

# 期待出力:
# ✅ All smoke tests passed!
#
# ✓ Health endpoint working
# ✓ Authentication working
# ✓ Templates API working with new schema
# ✓ Job creation and status check working
# ✓ Token limit enforced (≤1500)
# ✓ Idempotency working
#
# 🚀 Preview environment is ready for UAT!
```

**✅ 成功**: exit code 0、全テスト Pass

**❌ 失敗**: ログを確認し、該当箇所を修正

---

### 5.2 手動curlスモークテスト（追加確認）

**以下のコマンドをコピー＆ペーストで順次実行**:

#### Test 1: Health Check

```bash
curl -s ${API_PREVIEW_BASE}/health | jq .

# 期待出力:
# {
#   "ok": true,
#   "version": "1.0.0-preview",
#   "git": "b114399"
# }
```

#### Test 2: Authentication

```bash
JWT=$(curl -s -X POST "$API_PREVIEW_BASE/api/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@example.com","password":"password123"}' \
  | jq -r '.access_token')

echo "JWT Token: ${JWT:0:30}..."

# 期待: JWT token が表示される
```

#### Test 3: Templates API - 新スキーマ確認

```bash
curl -s -H "Authorization: Bearer $JWT" \
  "$API_PREVIEW_BASE/api/v1/templates?category=LP&size=5" \
  | jq '{
    count: .templates|length,
    total: .total,
    first_template: .templates[0] | {id, name, category, fields}
  }'

# 期待出力:
# {
#   "count": 5,
#   "total": 30,
#   "first_template": {
#     "id": "tpl_xxx",
#     "name": "Sample Template",
#     "category": "LP",
#     "fields": [...]
#   }
# }
```

#### Test 4: Job Creation + Idempotency

```bash
# Idempotency Key生成
IDEMPOTENCY_KEY="smoke-test-$(date +%s)"

# Job作成
JOB_RESPONSE=$(curl -s -X POST "$API_PREVIEW_BASE/api/v1/templates/tpl_001/use" \
  -H "Authorization: Bearer $JWT" \
  -H 'Content-Type: application/json' \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  -d "{
    \"template_id\": \"tpl_001\",
    \"inputs\": {\"title\": \"Smoke Test\"},
    \"temperature\": 0.7,
    \"intensity\": \"medium\",
    \"idempotency_key\": \"$IDEMPOTENCY_KEY\"
  }")

JOB_ID=$(echo $JOB_RESPONSE | jq -r '.job_id')
JOB_STATUS=$(echo $JOB_RESPONSE | jq -r '.status')

echo "Job ID: $JOB_ID"
echo "Initial Status: $JOB_STATUS"

# 期待: status が "pending"
```

#### Test 5: Job Status Check

```bash
# 3秒待機
sleep 3

# Job ステータス確認
curl -s -H "Authorization: Bearer $JWT" \
  "$API_PREVIEW_BASE/api/v1/jobs/$JOB_ID" \
  | jq '{job_id, status, usage}'

# 期待出力:
# {
#   "job_id": "job_xxx",
#   "status": "processing" または "completed",
#   "usage": {
#     "total_tokens": 1234,  # ≤1500
#     "estimated_cost_usd": 0.0123
#   }
# }
```

#### Test 6: Idempotency Check

```bash
# 同じ Idempotency-Key で再実行
JOB_RESPONSE_2=$(curl -s -X POST "$API_PREVIEW_BASE/api/v1/templates/tpl_001/use" \
  -H "Authorization: Bearer $JWT" \
  -H 'Content-Type: application/json' \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  -d "{
    \"template_id\": \"tpl_001\",
    \"inputs\": {\"title\": \"Smoke Test\"},
    \"temperature\": 0.7,
    \"intensity\": \"medium\",
    \"idempotency_key\": \"$IDEMPOTENCY_KEY\"
  }")

JOB_ID_2=$(echo $JOB_RESPONSE_2 | jq -r '.job_id')

echo "Original Job ID: $JOB_ID"
echo "Duplicate Job ID: $JOB_ID_2"

# 期待: JOB_ID == JOB_ID_2（同じJobが返る）
```

---

### 5.3 異常系テスト（任意）

#### Test 7: 422 Token Budget Exceeded

```bash
# 大量入力でトークン超過を発生
curl -s -X POST "$API_PREVIEW_BASE/api/v1/templates/tpl_001/use" \
  -H "Authorization: Bearer $JWT" \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: smoke-test-token-exceeded' \
  -d "{
    \"template_id\": \"tpl_001\",
    \"inputs\": {\"title\": \"$(python3 -c 'print(\"A\"*10000)')\"},
    \"temperature\": 1.0,
    \"intensity\": \"high\",
    \"idempotency_key\": \"smoke-test-token-exceeded\"
  }" | jq .

# 期待出力:
# {
#   "code": "TOKEN_BUDGET_EXCEEDED",
#   "message": "Agent1 token limit exceeded: ...",
#   "details": {...}
# }
```

#### Test 8: 429 Rate Limit

```bash
# 連続リクエストでレート制限発動
for i in {1..10}; do
  curl -s -X POST "$API_PREVIEW_BASE/api/v1/templates/tpl_001/use" \
    -H "Authorization: Bearer $JWT" \
    -H 'Content-Type: application/json' \
    -H "Idempotency-Key: smoke-test-ratelimit-$i" \
    -d "{
      \"template_id\": \"tpl_001\",
      \"inputs\": {\"title\": \"Rate Test $i\"},
      \"temperature\": 0.7,
      \"intensity\": \"low\",
      \"idempotency_key\": \"smoke-test-ratelimit-$i\"
    }" > /dev/null &
done

wait

# 期待: 一部が 429 Too Many Requests を返す
```

---

## 📢 Phase 6: UAT準備（15分）

### 6.1 テスターアカウント作成

**Google Sheets Users シートに手動追加**:

| id | email | password_hash | role | monthly_quota | created_at |
|----|-------|---------------|------|---------------|------------|
| usr_uat_001 | tester1@example.com | `$2b$12$...` | user | 50 | 2025-10-16T00:00:00Z |
| usr_uat_002 | tester2@example.com | `$2b$12$...` | user | 50 | 2025-10-16T00:00:00Z |
| usr_uat_003 | tester3@example.com | `$2b$12$...` | user | 50 | 2025-10-16T00:00:00Z |
| usr_uat_admin | tester_admin@example.com | `$2b$12$...` | admin | 200 | 2025-10-16T00:00:00Z |

**BCrypt ハッシュ生成**:

```bash
# Python で BCrypt ハッシュ生成
python3 << 'EOF'
import bcrypt
passwords = {
    "tester1": "password123",
    "tester2": "password123",
    "tester3": "password123",
    "admin": "admin123"
}
for user, pwd in passwords.items():
    hashed = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
    print(f"{user}: {hashed}")
EOF
```

**ログインテスト**:

```bash
# tester1 でログイン
curl -s -X POST "$API_PREVIEW_BASE/api/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"tester1@example.com","password":"password123"}' \
  | jq .

# 期待: access_token が返る
```

### 6.2 UAT告知作成・送信

**メール/Slackテンプレート**:

```
件名: 【UAT開始】tepure Preview環境テスト実施のお願い

皆様

お疲れ様です。tepure（Figmaテンプレート自動化システム）のPreview環境が準備完了しました。
本日よりUATを開始しますので、ご協力をお願いいたします。

■ UAT期間
2025-10-16（水）〜 2025-10-18（金）17:00

■ Preview環境URL
- Frontend: $FRONTEND_PREVIEW_URL
- API: $API_PREVIEW_BASE

■ テスターアカウント
（個別に配布します）

■ テスト項目
docs/UAT_CHECKLIST.md を参照

重点確認:
- Templates一覧でcategoryフィルター動作
- Template詳細でfields配列表示
- Job作成後、status遷移（pending→processing→completed）
- /health エンドポイント正常レスポンス
- Token制限動作（≤1500）

■ 不具合報告
GitHub Issues: https://github.com/your-org/tepure/issues
ラベル: uat, P0/P1/P2
スクリーンショット/動画を添付してください

■ 緊急連絡先
Email: owner@example.com
Slack: #tepure-uat

よろしくお願いいたします。
```

**送信**:

```bash
# Slack投稿（例）
# slack-cli を使用する場合:
# slack-cli chat post --channel #tepure-uat --text "$(cat uat-announcement.txt)"

# または手動でコピー＆ペーストして送信
```

### 6.3 GitHub Issue 作成

```bash
# GitHub CLI で UAT Issue 作成
gh issue create \
  --title "UAT Ready - Preview Environment (2025-10-16)" \
  --label "uat,preview,testing" \
  --body "## 🚀 Preview Environment Ready for UAT

Smoke tests have passed successfully. Preview environment is ready for UAT.

### Environment URLs
- **Frontend**: $FRONTEND_PREVIEW_URL
- **API**: $API_PREVIEW_BASE

### Smoke Test Results
- ✅ Health Check
- ✅ Authentication
- ✅ Templates API (new schema validated)
- ✅ Jobs API (status vocabulary validated)
- ✅ Token limit enforcement
- ✅ Idempotency

### UAT Period
**Start**: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
**End**: TBD (typically 2-3 days)

### Test Accounts
- tester1@example.com
- tester2@example.com
- tester3@example.com
- tester_admin@example.com (admin role)

### Critical Test Items
- [ ] Templates category filter (LP/Banner/SNS/WebApp)
- [ ] Template fields array display
- [ ] Job status transitions (pending→processing→completed)
- [ ] Token budget enforcement (≤1500)
- [ ] /health endpoint format

### Reporting Issues
Create new issues with:
- Label: \`uat\`
- Priority: \`P0\` (critical), \`P1\` (high), \`P2\` (medium)
- Include: Screenshots/videos, steps to reproduce

cc: @project-owner @uat-team
"

# ✅ 成功: Issue URL が表示される
```

---

## ✅ 完了確認

### 全Phase完了チェック

- [ ] Phase 1: Secrets Preflight 成功
- [ ] Phase 2: Sheets バックアップ完了
- [ ] Phase 3: マイグレーション2本成功
- [ ] Phase 4: Preview デプロイ完了（API + Frontend）
- [ ] Phase 5: スモークテスト全Pass
- [ ] Phase 6: UAT準備完了（告知送信 + アカウント配布）

### 環境URL記録

```
API Preview URL: _______________________________________
Frontend Preview URL: _______________________________________
UAT Issue URL: _______________________________________
```

### 実施時刻記録

| Phase | 開始時刻 | 完了時刻 |
|-------|---------|---------|
| Preflight | __:__ | __:__ |
| Backup | __:__ | __:__ |
| Migration | __:__ | __:__ |
| Deploy | __:__ | __:__ |
| Smoke Test | __:__ | __:__ |
| UAT Prep | __:__ | __:__ |

---

## 🚨 トラブルシューティング

### Preflight失敗

**症状**: `ops/check-secrets.py` が exit 1

**対処**:
```bash
# 不足キー確認
python3 ops/check-secrets.py --source file --file .env

# .env に追加
vim .env  # または nano .env

# 再チェック
python3 ops/check-secrets.py --source file --file .env --json
```

### マイグレーション失敗

**症状**: `status: "failed"`

**対処**:
```bash
# ロールバック実行
python -m app.migrations.20251016_templates_extend down
python -m app.migrations.20251016_jobs_status_map down

# バックアップから復元（最終手段）
# Google Sheets → ファイル → バージョン履歴 → 復元
```

### デプロイ失敗

**症状**: Cloud Run デプロイエラー

**対処**:
```bash
# ログ確認
gcloud run services logs read tepure-api-preview \
  --region $GCP_REGION \
  --limit=50

# イメージ存在確認
gcloud artifacts docker images list \
  asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/tepure

# Secrets存在確認
gcloud secrets list | grep -E 'jwt-secret|anthropic-key'
```

### スモークテスト失敗

**症状**: `smoke-test.sh` が exit 1

**対処**:
```bash
# 個別テスト実行で原因特定
curl -s ${API_PREVIEW_BASE}/health | jq .

# ログ確認
gcloud run services logs read tepure-api-preview \
  --region $GCP_REGION \
  --limit=50 \
  --format=json | jq .
```

---

## 📚 参考ドキュメント

- **詳細手順**: `docs/DEPLOYMENT_RUNBOOK.md`
- **マイグレーションガイド**: `docs/MIGRATION_GUIDE.md`
- **実装サマリー**: `docs/DIFFERENTIAL_UPDATE_SUMMARY.md`
- **UAT チェックリスト**: `docs/UAT_CHECKLIST.md`
- **運用チェックリスト**: `docs/OPERATIONS_CHECKLIST.md`

---

## 🎉 完了

**全Phase完了おめでとうございます！**

UAT を開始し、テスターからのフィードバックを収集してください。

重大な不具合（P0）が発生した場合は、即座にロールバックを実施してください。

---

**作成者**: Claude Code
**バージョン**: 1.0.0
**最終更新**: 2025-10-16
