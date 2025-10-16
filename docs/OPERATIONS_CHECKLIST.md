# 本日の運用実施チェックリスト

**実施日**: 2025-10-16
**目的**: 差分コミット（b114399, d152f5e）をPreview環境へ展開し、UAT開始

---

## 📋 事前準備（実施前に確認）

### ✅ 環境変数確認

```bash
# 必須環境変数が設定されているか確認
echo $GCP_PROJECT_ID        # Google Cloud プロジェクトID
echo $ANTHROPIC_API_KEY     # Claude API キー
echo $FIGMA_API_TOKEN       # Figma APIトークン
```

### ✅ Secrets確認（GitHub Secrets / Cloud Run）

- [ ] `JWT_SECRET`
- [ ] `REFRESH_SECRET`
- [ ] `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64`
- [ ] `FIGMA_API_TOKEN`
- [ ] `LLM_API_KEY`
- [ ] `SHEETS_USERS_ID`
- [ ] `SHEETS_TEMPLATES_ID`
- [ ] `SHEETS_JOBS_ID`
- [ ] `SHEETS_AUDITLOGS_ID`

### ✅ 新規Secrets追加（監視閾値）

- [ ] `ERROR_RATE_THRESHOLD=0.05`
- [ ] `ERROR_RATE_WINDOW_MINUTES=5`
- [ ] `LATENCY_P95_THRESHOLD_MS=2000`
- [ ] `DAILY_COST_THRESHOLD_USD=50.0`

---

## 🔄 Phase 1: バックアップ（必須）

### Google Sheets バックアップ

**実施時刻**: __________

- [ ] Users シートをCSV/Excelエクスポート
- [ ] Templates シートをCSV/Excelエクスポート
- [ ] Jobs シートをCSV/Excelエクスポート
- [ ] AuditLogs シートをCSV/Excelエクスポート

**バックアップ保存先**: `backups/2025-10-16/`

**確認コマンド**:
```bash
ls -lh backups/2025-10-16/
# 期待: 4つのCSV/Excelファイルが存在
```

---

## 🚀 Phase 2: マイグレーション実行

### 2.1 Templates スキーマ拡張

**実施時刻**: __________

```bash
cd backend
source venv/bin/activate
export $(cat ../.env | grep -v '^#' | xargs)
python -m app.migrations.20251016_templates_extend
```

**期待結果**:
```json
{
  "migration": "20251016_templates_extend",
  "status": "completed",
  "total_rows": XX,
  "updated_rows": XX
}
```

- [ ] `status: "completed"` を確認
- [ ] `updated_rows > 0` を確認
- [ ] エラーがないことを確認

**ロールバックコマンド（失敗時のみ）**:
```bash
python -m app.migrations.20251016_templates_extend down
```

### 2.2 Jobs ステータス変換

**実施時刻**: __________

```bash
python -m app.migrations.20251016_jobs_status_map
```

**期待結果**:
```json
{
  "migration": "20251016_jobs_status_map",
  "status": "completed",
  "total_rows": XX,
  "updated_rows": XX,
  "error_count": 0
}
```

- [ ] `status: "completed"` を確認
- [ ] `error_count: 0` を確認

**ロールバックコマンド（失敗時のみ）**:
```bash
python -m app.migrations.20251016_jobs_status_map down
```

### 2.3 手動データ更新

**実施時刻**: __________

**Google Sheets で以下を手動設定**:

#### Templates シート更新

- [ ] 全テンプレートに `category` 設定（LP/Banner/SNS/WebApp）
- [ ] 主要テンプレートに `fields` JSON配列設定
- [ ] 可能な範囲で `preview_url` 設定
- [ ] 可能な範囲で `figma_node_id` 設定

**fields JSON例**:
```json
[{"type":"text","label":"タイトル","default_value":"Sample"}]
```

---

## 🏗️ Phase 3: Preview デプロイ

### 3.1 Backend API デプロイ

**実施時刻**: __________

```bash
cd backend

# Docker イメージビルド & プッシュ
gcloud builds submit \
  --tag asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/tepure/api:preview-20251016

# Cloud Run デプロイ
gcloud run deploy tepure-api-preview \
  --image asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/tepure/api:preview-20251016 \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 5 \
  --timeout 60 \
  --set-env-vars "ENV=preview,APP_VERSION=1.0.0-preview,ERROR_RATE_THRESHOLD=0.05,ERROR_RATE_WINDOW_MINUTES=5,LATENCY_P95_THRESHOLD_MS=2000,DAILY_COST_THRESHOLD_USD=50.0" \
  --set-secrets "JWT_SECRET=jwt-secret:latest,REFRESH_SECRET=refresh-secret:latest,GOOGLE_SERVICE_ACCOUNT_JSON_BASE64=google-sa-json:latest,FIGMA_API_TOKEN=figma-token:latest,LLM_API_KEY=anthropic-key:latest,SHEETS_USERS_ID=sheets-users-id:latest,SHEETS_TEMPLATES_ID=sheets-templates-id:latest,SHEETS_JOBS_ID=sheets-jobs-id:latest,SHEETS_AUDITLOGS_ID=sheets-auditlogs-id:latest"
```

- [ ] ビルド成功（`gcloud builds list --limit=1` で確認）
- [ ] デプロイ成功（`Service URL: https://...` が表示）
- [ ] URL を記録: __________________________________________

**API Base URL**:
```bash
export API_PREVIEW_BASE=$(gcloud run services describe tepure-api-preview \
  --region asia-northeast1 \
  --format 'value(status.url)')

echo "API Preview URL: $API_PREVIEW_BASE"
```

### 3.2 Frontend デプロイ

**実施時刻**: __________

```bash
cd frontend

# 環境変数設定
echo "VITE_API_BASE=$API_PREVIEW_BASE" > .env.preview

# ビルド
npm ci
npm run build

# Firebase Preview チャネルにデプロイ
firebase hosting:channel:deploy preview-20251016 --expires 7d
```

- [ ] ビルド成功（`dist/` にファイル生成）
- [ ] デプロイ成功（Preview URL が表示）
- [ ] URL を記録: __________________________________________

---

## 🧪 Phase 4: スモークテスト

### 4.1 自動スモークテスト実行

**実施時刻**: __________

```bash
./scripts/smoke-test.sh $API_PREVIEW_BASE
```

**期待結果**:
```
✅ All smoke tests passed!

✓ Health endpoint working
✓ Authentication working
✓ Templates API working with new schema
✓ Job creation and status check working
✓ Token limit enforced (≤1500)
✓ Idempotency working

🚀 Preview environment is ready for UAT!
```

- [ ] テスト成功（exit code 0）
- [ ] 全テスト項目が ✅ Pass

### 4.2 手動スモークテスト（追加確認）

**実施時刻**: __________

#### Health Check

```bash
curl -s ${API_PREVIEW_BASE}/health | jq .
```

**期待**:
```json
{
  "ok": true,
  "version": "1.0.0-preview",
  "git": "b114399"
}
```

- [ ] `ok: true`
- [ ] `version` が正しい
- [ ] `git` ハッシュが正しい

#### Templates API - 新スキーマ確認

```bash
JWT=$(curl -s -X POST "$API_PREVIEW_BASE/api/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@example.com","password":"password123"}' \
  | jq -r '.access_token')

curl -s -H "Authorization: Bearer $JWT" \
  "$API_PREVIEW_BASE/api/v1/templates?size=1" \
  | jq '.templates[0] | {id, category, fields, preview_url}'
```

**期待**:
```json
{
  "id": "tpl_xxx",
  "category": "LP",
  "fields": [...],
  "preview_url": "https://..."
}
```

- [ ] `category` が存在（LP/Banner/SNS/WebApp）
- [ ] `fields` 配列が存在
- [ ] `preview_url` が存在

---

## 📢 Phase 5: UAT準備

### 5.1 テスターアカウント作成

**実施時刻**: __________

**Google Sheets Users シートに手動追加**:

| email | password_hash | role | monthly_quota |
|-------|---------------|------|---------------|
| tester1@example.com | (BCrypt hash) | user | 50 |
| tester2@example.com | (BCrypt hash) | user | 50 |
| tester3@example.com | (BCrypt hash) | user | 50 |
| tester_admin@example.com | (BCrypt hash) | admin | 200 |

- [ ] 4アカウント作成完了
- [ ] パスワードを安全に記録
- [ ] ログインテスト実施

### 5.2 UAT告知作成・送信

**実施時刻**: __________

**送信先**:
- [ ] Slack #tepure-uat チャネル
- [ ] Email to UAT team
- [ ] GitHub Issue 作成

**告知内容**（テンプレート）:

```
件名: 【UAT開始】tepure Preview環境テスト実施のお願い

■ UAT期間
2025-10-16（水）〜 2025-10-18（金）17:00

■ Preview環境URL
- Frontend: [FRONTEND_PREVIEW_URL]
- API: [API_PREVIEW_BASE]

■ テスト項目
docs/UAT_CHECKLIST.md 参照
重点: category フィルター、fields表示、status遷移、/health

■ 不具合報告
GitHub Issues: https://github.com/your-org/tepure/issues
ラベル: uat, P0/P1/P2
```

- [ ] Slack投稿完了
- [ ] Email送信完了
- [ ] GitHub Issue作成完了
- [ ] テスターアカウント配布完了

### 5.3 UAT監視体制

**実施時刻**: __________

- [ ] GitHub Issues 監視開始
- [ ] Cloud Monitoring アラート有効化
- [ ] Slack #tepure-uat チャネル監視
- [ ] 緊急連絡先共有（P0 Issue時）

---

## ✅ Phase 6: 受け入れチェックリスト

### スモーク & データ移行

- [ ] Google Sheets 4表バックアップ完了
- [ ] `20251016_templates_extend` 実行ログOK
- [ ] `20251016_jobs_status_map` 実行ログOK
- [ ] `/health` が `{ ok: true, version, git }` を返す

### API/機能

- [ ] `GET /api/v1/templates` の配列キーが `templates`
- [ ] Template に `category`, `fields`, `preview_url` が含まれる
- [ ] `POST /use` → `GET /jobs/{id}` で `completed` まで到達
- [ ] Job status が新語彙使用（pending/processing/completed/failed）
- [ ] Idempotency-Key 重複で再実行されない
- [ ] 422 Token Budget Exceeded エラーが適切に返却

### 監視/コスト

- [ ] 監視閾値がENVに設定（0.05/2000ms/$50）
- [ ] 1ジョブあたり `tokens <= 1500` を確認

### UAT準備

- [ ] テスター3〜5名にアカウント配布
- [ ] UAT告知（URL・期間・報告フォーム）送信
- [ ] 重大Issue（P0）時の連絡線共有

---

## 📝 実施記録

### タイムライン

| 時刻 | Phase | ステータス | 備考 |
|------|-------|----------|------|
| __:__ | Phase 1 | [ ] 完了 | バックアップ |
| __:__ | Phase 2 | [ ] 完了 | マイグレーション |
| __:__ | Phase 3 | [ ] 完了 | デプロイ |
| __:__ | Phase 4 | [ ] 完了 | スモークテスト |
| __:__ | Phase 5 | [ ] 完了 | UAT準備 |
| __:__ | Phase 6 | [ ] 完了 | 受け入れチェック |

### 実施者

- **オーナー**: __________________
- **監視者**: __________________
- **承認者**: __________________

### 問題・エスカレーション記録

| 時刻 | 問題内容 | 対応 | ステータス |
|------|---------|------|----------|
|      |         |      |          |

---

## 🚨 トラブルシューティング

### マイグレーション失敗時

```bash
# ロールバック実行
python -m app.migrations.20251016_templates_extend down
python -m app.migrations.20251016_jobs_status_map down

# バックアップから復元（最終手段）
# Google Sheets → ファイル → バージョン履歴 → 復元
```

### デプロイ失敗時

```bash
# 前回のリビジョンにロールバック
gcloud run services update-traffic tepure-api-preview \
  --to-revisions=PREVIOUS_REVISION=100 \
  --region asia-northeast1

# または直前のイメージで再デプロイ
```

### スモークテスト失敗時

- **Health Check失敗**: Cloud Run ログ確認、環境変数確認
- **Authentication失敗**: JWT_SECRET確認、Users シート確認
- **Templates API失敗**: マイグレーション成功確認、Sheets API権限確認
- **Jobs API失敗**: LLM_API_KEY確認、トークン制限確認

---

## 📚 参考ドキュメント

- **完全な手順**: `docs/DEPLOYMENT_RUNBOOK.md`
- **マイグレーションガイド**: `docs/MIGRATION_GUIDE.md`
- **実装サマリー**: `docs/DIFFERENTIAL_UPDATE_SUMMARY.md`
- **UAT チェックリスト**: `docs/UAT_CHECKLIST.md`

---

## 🎉 完了判定

**全Phase完了時**:
- [ ] 全チェック項目が ✅
- [ ] スモークテスト全パス
- [ ] UAT告知送信完了
- [ ] テスターアカウント配布完了

**→ UAT開始可能！**

---

**実施日**: 2025-10-16
**作成者**: Claude Code
**バージョン**: 1.0.0
