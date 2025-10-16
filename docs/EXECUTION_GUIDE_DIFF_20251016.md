# 完全実行ガイド - 差分修正 (2025-10-16)

このドキュメントは `COMPLETE_EXECUTION_GUIDE.md` への差分修正を記載します。

---

## 📝 修正サマリ

### 環境変数名の統一
- `LLM_API_KEY` → **`ANTHROPIC_API_KEY`** (プロバイダ特定のため)
- `GIT_COMMIT` → **`GIT_SHA`** (/health の git フィールドに反映)

### API仕様の修正
- `intensity`: 文字列 `"low|medium|high"` → **整数 `1-10`**
- `/health` レスポンス: **3キーのみ** (`ok`, `version`, `git`)

### Idempotency
- ヘッダー `Idempotency-Key: <uuid>` 必須
- 同一キーは同一 `job_id` を返却（重複は409）

---

## 🔧 Phase 1: Secrets Preflight の修正

### 1.1 .env.required の更新（既に反映済み）

```bash
# 修正後の ops/.env.required

# ==== LLM API (1項目) ====
ANTHROPIC_API_KEY  # ← LLM_API_KEY から変更
```

### 1.2 ローカル .env ファイル確認

```bash
# 旧キー名がある場合は新キー名にコピー
if grep -q "LLM_API_KEY=" .env; then
    echo "⚠️  LLM_API_KEY found. Copying to ANTHROPIC_API_KEY..."
    LLM_VALUE=$(grep "LLM_API_KEY=" .env | cut -d'=' -f2-)
    if ! grep -q "ANTHROPIC_API_KEY=" .env; then
        echo "ANTHROPIC_API_KEY=$LLM_VALUE" >> .env
    fi
fi

# 新キー名でチェック
python3 ops/check-secrets.py --source file --file .env --json
```

**期待出力**:
```json
{
  "ok": true,
  "missing": [],
  "warnings": [],
  "format_issues": [],
  "checked": [
    "ANTHROPIC_API_KEY",  // ← 新キー名
    "GIT_SHA",           // ← 新キー名
    ...
  ]
}
```

---

## 🚀 Phase 4: Preview デプロイの修正

### 4.2 Cloud Run デプロイコマンド（修正版）

```bash
# Git SHA を取得
export GIT_SHA=$(git rev-parse --short HEAD)

# Cloud Run デプロイ（修正版）
gcloud run deploy tepure-api-preview \
  --image asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/tepure/api:preview-20251016 \
  --region $GCP_REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 5 \
  --timeout 60 \
  --set-env-vars "\
ENV=preview,\
APP_VERSION=1.0.0-preview,\
GIT_SHA=$GIT_SHA,\
ERROR_RATE_THRESHOLD=0.05,\
ERROR_RATE_WINDOW_MINUTES=5,\
LATENCY_P95_THRESHOLD_MS=2000,\
DAILY_COST_THRESHOLD_USD=50.0" \
  --set-secrets "\
JWT_SECRET=jwt-secret:latest,\
REFRESH_SECRET=refresh-secret:latest,\
GOOGLE_SERVICE_ACCOUNT_JSON_BASE64=google-sa-json:latest,\
FIGMA_API_TOKEN=figma-token:latest,\
ANTHROPIC_API_KEY=anthropic-key:latest,\
SHEETS_USERS_ID=sheets-users-id:latest,\
SHEETS_TEMPLATES_ID=sheets-templates-id:latest,\
SHEETS_JOBS_ID=sheets-jobs-id:latest,\
SHEETS_AUDITLOGS_ID=sheets-auditlogs-id:latest" \
  --project $GCP_PROJECT_ID
```

**変更点**:
1. `LLM_API_KEY` → **`ANTHROPIC_API_KEY`** (Secret Manager のシークレット名も対応必要)
2. `GIT_COMMIT` → **`GIT_SHA`** (環境変数名を統一)
3. 環境変数として `GIT_SHA=$GIT_SHA` を明示的に設定

### 4.3 Secret Manager の確認

```bash
# Secret Manager にシークレットが存在するか確認
gcloud secrets list --project=$GCP_PROJECT_ID | grep anthropic-key

# 存在しない場合は作成
if [ $? -ne 0 ]; then
    echo "Creating ANTHROPIC_API_KEY secret..."
    echo -n "your-anthropic-api-key" | \
        gcloud secrets create anthropic-key \
        --data-file=- \
        --project=$GCP_PROJECT_ID
fi

# 既存の llm-api-key がある場合はコピー
# (手動で実施：Secret Manager GUI で llm-api-key の値を anthropic-key にコピー)
```

---

## 🧪 Phase 5: スモークテスト の修正

### 5.1 更新版スモークテストの使用

```bash
# 更新版スモークテストスクリプトを使用
export API_BASE="https://tepure-api-preview-xxx.run.app"
bash scripts/smoke-test-updated.sh
```

**主な変更点**:
1. `/health` が 3キー (ok, version, git) のみ返すことを検証
2. `intensity` を整数 (1-10) で送信: `"intensity": 7`
3. Idempotency テストを追加（同じキーで同じ job_id）
4. 422 Token Budget テストを追加（大量テキスト送信）
5. 429 Rate Limit テストを追加（6連続リクエスト）

### 5.2 curl テスト例（修正版）

#### Test 1: Health Check
```bash
curl -s "${API_BASE}/health" | jq '.'

# 期待出力（3キーのみ）:
{
  "ok": true,
  "version": "1.0.0-preview",
  "git": "a1b2c3d"
}
```

#### Test 2: Create Job with Intensity (整数)
```bash
curl -X POST "${API_BASE}/api/v1/use" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "template_id": "tpl_001",
    "inputs": {
      "title": "Test Title",
      "description": "Test Description"
    },
    "temperature": 0.7,
    "intensity": 7
  }' | jq '.'

# 期待出力:
{
  "job_id": "job_20251016140000",
  "status": "pending",
  ...
}
```

#### Test 3: Idempotency Test
```bash
# 同じキーで2回リクエスト
IDEM_KEY="test-idempotency-$(date +%s)"

# 1回目
JOB1=$(curl -s -X POST "${API_BASE}/api/v1/use" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: ${IDEM_KEY}" \
  -d '{
    "template_id": "tpl_001",
    "inputs": {"title": "Test"},
    "temperature": 0.7,
    "intensity": 5
  }')

JOB_ID1=$(echo "$JOB1" | jq -r '.job_id')

# 2回目（同じキー）
JOB2=$(curl -s -X POST "${API_BASE}/api/v1/use" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: ${IDEM_KEY}" \
  -d '{
    "template_id": "tpl_001",
    "inputs": {"title": "Test"},
    "temperature": 0.7,
    "intensity": 5
  }')

JOB_ID2=$(echo "$JOB2" | jq -r '.job_id')

# 検証
if [ "$JOB_ID1" == "$JOB_ID2" ]; then
    echo "✓ Idempotency working: $JOB_ID1"
else
    echo "✗ Idempotency FAILED: $JOB_ID1 != $JOB_ID2"
fi
```

#### Test 4: 422 Token Budget Exceeded
```bash
# 大量テキストで送信
LARGE_TEXT=$(python3 -c "print('A' * 12000)")

curl -X POST "${API_BASE}/api/v1/use" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d "{
    \"template_id\": \"tpl_001\",
    \"inputs\": {
      \"title\": \"${LARGE_TEXT}\"
    },
    \"temperature\": 1.0,
    \"intensity\": 10
  }" | jq '.'

# 期待出力:
{
  "error": {
    "code": "TOKEN_BUDGET_EXCEEDED",
    "message": "Token budget exceeded: 1200 > 900",
    "hint": "Reduce input size or simplify the request",
    "meta": {
      "estimated_tokens": 1200,
      "budget_tokens": 900,
      "agent": "Agent1"
    }
  }
}
```

#### Test 5: 429 Rate Limit
```bash
# 6回連続リクエスト（5 req/min を超過）
for i in {1..6}; do
    echo "Request #$i..."
    curl -s -o /dev/null -w "%{http_code}\n" -X POST "${API_BASE}/api/v1/use" \
      -H "Authorization: Bearer ${TOKEN}" \
      -H "Content-Type: application/json" \
      -H "Idempotency-Key: rate-test-$i-$(date +%s)" \
      -d "{
        \"template_id\": \"tpl_001\",
        \"inputs\": {\"title\": \"Rate Test $i\"},
        \"temperature\": 0.5,
        \"intensity\": 5
      }"
    sleep 0.5
done

# 期待: 少なくとも1回は 429 を返す
```

---

## 📊 Phase 6: UAT準備 の追加項目

### 6.1 環境変数名の確認

UAT チェックリストに以下を追加:

```markdown
## 環境変数確認

- [ ] `ANTHROPIC_API_KEY` が設定されている（LLM_API_KEY ではない）
- [ ] `GIT_SHA` が設定されている（GIT_COMMIT ではない）
- [ ] `/health` が `{ok, version, git}` の3キーのみ返す
```

### 6.2 intensity の範囲確認

```markdown
## API仕様確認

- [ ] `intensity` を整数 1-10 で送信できる
- [ ] `intensity=1` (最小) で動作する
- [ ] `intensity=10` (最大) で動作する
- [ ] `intensity=0` でバリデーションエラー（400）
- [ ] `intensity=11` でバリデーションエラー（400）
```

---

## 🔄 Phase 8: ロールバック の修正

### 8.1 環境変数のロールバック

ロールバック時は古いリビジョンが `LLM_API_KEY` を使用している可能性があるため、
**両方の環境変数を設定**しておく（後方互換性）:

```bash
# ロールバック後、両方の環境変数を設定
gcloud run services update tepure-api-preview \
  --region $GCP_REGION \
  --update-secrets "\
LLM_API_KEY=anthropic-key:latest,\
ANTHROPIC_API_KEY=anthropic-key:latest" \
  --project $GCP_PROJECT_ID
```

---

## 📋 チェックリスト（差分）

### Phase 1: Secrets Preflight
- [ ] `ANTHROPIC_API_KEY` が .env に存在する
- [ ] `GIT_SHA` が環境変数として設定できる
- [ ] `ops/check-secrets.py` が成功する

### Phase 4: Preview デプロイ
- [ ] Secret Manager に `anthropic-key` が存在する
- [ ] `--set-secrets` で `ANTHROPIC_API_KEY` を指定
- [ ] `--set-env-vars` で `GIT_SHA` を指定

### Phase 5: スモークテスト
- [ ] `/health` が 3キーのみ返す
- [ ] `intensity` を整数で送信できる
- [ ] Idempotency が動作する（同じ job_id）
- [ ] 422 Token Budget エラーが発生する
- [ ] 429 Rate Limit エラーが発生する

### Phase 6: UAT
- [ ] intensity 1-10 の全範囲で動作する
- [ ] intensity 0/11 でバリデーションエラー

---

## 🆕 新規追加ファイル

1. **`scripts/smoke-test-updated.sh`** - 更新版スモークテストスクリプト
   - `/health` 3キー検証
   - intensity 整数対応
   - Idempotency テスト
   - 422/429 エラーテスト

2. **`docs/EXECUTION_GUIDE_DIFF_20251016.md`** - このドキュメント

---

## 📚 参考

- 元ガイド: `docs/COMPLETE_EXECUTION_GUIDE.md`
- API curl例: `docs/API_CURL_EXAMPLES.md`
- 実装サマリ: `docs/IMPLEMENTATION_SUMMARY_20251016.md`

---

**更新日**: 2025-10-16
**対象バージョン**: 1.0.0-preview
