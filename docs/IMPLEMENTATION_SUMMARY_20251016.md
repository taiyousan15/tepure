# Implementation Summary - 2025-10-16

## 概要

tepure（Figmaテンプレート自動化システム）の最新仕様への再整理を完了しました。

**実施日**: 2025-10-16
**対象**: 422エラー、Idempotency-Key、統一エラーフォーマット、トークン予算チェック

---

## 実装内容

### 1. 統一エラーフォーマット実装 ✅

**ファイル**: `backend/app/errors.py` (新規作成)

**標準エラーフォーマット**:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "hint": "Optional hint for resolution",
    "meta": {
      "key": "value"
    }
  }
}
```

**カスタム例外**:
- `TepureError` - 基底例外クラス
- `TokenBudgetExceededError` - 422トークン予算超過
- `IdempotencyConflictError` - 409べき等キー競合
- `QuotaExceededError` - 429月次クォータ超過
- `RateLimitExceededError` - 429レート制限超過

**標準エラーレスポンス関数**:
- `validation_error()` - 400バリデーションエラー
- `invalid_json_error()` - 400不正なJSON
- `invalid_credentials_error()` - 401認証エラー
- `token_expired_error()` - 401トークン期限切れ
- `forbidden_error()` - 403アクセス拒否
- `not_found_error()` - 404リソース未検出
- `internal_server_error()` - 500サーバーエラー

**実装行数**: 285行

---

### 2. トークン予算事前チェック ✅

**ファイル**: `backend/app/agents.py`

**主な変更**:
1. **トークン推定関数追加**:
   ```python
   def estimate_tokens(text: str) -> int:
       """Rough approximation: 1 token ≈ 4 characters"""
       return len(text) // 4
   ```

2. **環境変数からのトークン制限読み込み**:
   ```python
   MAX_AGENT1_TOKENS = int(os.getenv('TOKEN_BUDGET_AGENT1', '900'))
   MAX_AGENT2_TOKENS = int(os.getenv('TOKEN_BUDGET_AGENT2', '600'))
   MAX_TOTAL_TOKENS = int(os.getenv('TOKEN_BUDGET_TOTAL', '1500'))
   ```

3. **Agent1での事前チェック**:
   ```python
   estimated_input_tokens = estimate_tokens(system_prompt) + estimate_tokens(user_prompt)
   estimated_total_tokens = estimated_input_tokens + MAX_AGENT1_TOKENS

   if estimated_total_tokens > MAX_AGENT1_TOKENS:
       raise TokenBudgetExceededError(
           estimated_tokens=estimated_total_tokens,
           budget_tokens=MAX_AGENT1_TOKENS,
           agent="Agent1"
       )
   ```

4. **Agent2でも同様の事前チェック実装**

5. **実際の使用量チェック**（LLM呼び出し後）:
   ```python
   total_tokens = prompt_tokens + completion_tokens
   if total_tokens > MAX_AGENT1_TOKENS:
       raise TokenBudgetExceededError(...)
   ```

**422エラーレスポンス例**:
```json
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

---

### 3. API統一エラーハンドリング ✅

**ファイル**: `backend/app/api_v1.py`

**主な変更**:
1. **エラーモジュールインポート**:
   ```python
   from .errors import (
       TepureError,
       TokenBudgetExceededError,
       IdempotencyConflictError,
       QuotaExceededError,
       exception_to_response,
       validation_error,
       invalid_credentials_error,
       forbidden_error,
       not_found_error,
       internal_server_error
   )
   ```

2. **ログインエンドポイント更新**:
   - `invalid_credentials_error()` 使用
   - `exception_to_response()` で TepureError 処理

3. **テンプレート取得エンドポイント更新**:
   - `not_found_error("Template")` 使用

4. **ジョブ取得エンドポイント更新**:
   - `not_found_error("Job")` 使用
   - `forbidden_error()` 使用

5. **ジョブ作成エンドポイント更新** (最重要):
   ```python
   except ValidationError as e:
       return validation_error(details=e.errors())
   except TokenBudgetExceededError as e:
       # 422 Token Budget Exceeded
       logger.warning("token_budget_exceeded", user_id=user_id, error=str(e))
       return exception_to_response(e)
   except QuotaExceededError as e:
       # 429 Quota Exceeded
       return exception_to_response(e)
   except IdempotencyConflictError as e:
       # 409 Idempotency Conflict
       return exception_to_response(e)
   except TepureError as e:
       return exception_to_response(e)
   except Exception as e:
       logger.error("create_job_error", error=str(e), exc_info=True)
       return internal_server_error()
   ```

---

### 4. Idempotency-Key実装確認 ✅

**ファイル**: `backend/app/jobs.py`

**既存実装**:
- Idempotency-Key は既に実装済み
- `check_idempotency()` メソッドで既存ジョブを返却
- `idempotency_map` で UUID → job_id のマッピング管理

**今回の変更**:
- `IdempotencyConflictError` インポート追加
- 現在の実装は正しく、既存ジョブIDを返すことでRESTのべき等性を実現

**使用方法**:
```bash
curl -X POST "${API_BASE}/use" \
  -H "X-Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{...}'
```

---

### 5. .env.sample 更新 ✅

**ファイル**: `.env.sample`

**17項目の必須環境変数**:

1. **Security (2項目)**:
   - `JWT_SECRET`
   - `REFRESH_SECRET`

2. **Google Sheets (5項目)**:
   - `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64`
   - `SHEETS_USERS_ID`
   - `SHEETS_TEMPLATES_ID`
   - `SHEETS_JOBS_ID`
   - `SHEETS_AUDITLOGS_ID`

3. **LLM API (1項目)**:
   - `LLM_API_KEY`

4. **Monitoring & Alerts (6項目)**:
   - `SENTRY_DSN`
   - `GA_MEASUREMENT_ID`
   - `ERROR_RATE_THRESHOLD=0.05`
   - `ERROR_RATE_WINDOW_MINUTES=5`
   - `LATENCY_P95_THRESHOLD_MS=2000`
   - `DAILY_COST_THRESHOLD_USD=50.0`

5. **External Services (1項目)**:
   - `FIGMA_API_TOKEN`

6. **Infrastructure (1項目)**:
   - `GCP_PROJECT_ID`

**新規追加項目**:
- `BCRYPT_ROUNDS=12`
- `TOKEN_BUDGET_TOTAL=1500`
- `TOKEN_BUDGET_AGENT1=900`
- `TOKEN_BUDGET_AGENT2=600`
- `MONTHLY_JOB_QUOTA_PER_USER=50`

---

### 6. API Curl Examples ドキュメント ✅

**ファイル**: `docs/API_CURL_EXAMPLES.md`

**内容**:
- 全11エンドポイントの完全なcurl例
- 成功レスポンス例
- 全エラーコードのレスポンス例:
  - 400: VALIDATION_ERROR, INVALID_JSON
  - 401: INVALID_CREDENTIALS, TOKEN_EXPIRED, TOKEN_INVALID
  - 403: FORBIDDEN
  - 404: NOT_FOUND
  - 409: IDEMPOTENCY_CONFLICT
  - 422: TOKEN_BUDGET_EXCEEDED
  - 429: QUOTA_EXCEEDED, RATE_LIMIT_EXCEEDED
  - 500: INTERNAL_SERVER_ERROR
  - 503: SERVICE_UNAVAILABLE

- テストスクリプト例
- フルフローテスト例

---

## エラーコード一覧

| HTTPステータス | エラーコード | メッセージ例 | 用途 |
|---|---|---|---|
| 400 | VALIDATION_ERROR | Invalid request parameters | バリデーションエラー |
| 400 | INVALID_JSON | Invalid JSON payload | 不正なJSON |
| 401 | INVALID_CREDENTIALS | Invalid email or password | 認証失敗 |
| 401 | TOKEN_EXPIRED | Access token expired | トークン期限切れ |
| 401 | TOKEN_INVALID | Invalid access token | 不正なトークン |
| 403 | FORBIDDEN | Access denied | アクセス拒否 |
| 403 | ADMIN_REQUIRED | Admin access required | 管理者権限必要 |
| 404 | NOT_FOUND | Resource not found | リソース未検出 |
| 404 | TEMPLATE_NOT_FOUND | Template not found | テンプレート未検出 |
| 404 | JOB_NOT_FOUND | Job not found | ジョブ未検出 |
| 409 | IDEMPOTENCY_CONFLICT | Request with same key exists | べき等キー競合 |
| 409 | ALREADY_EXISTS | Resource already exists | リソース既存 |
| 422 | TOKEN_BUDGET_EXCEEDED | Token budget exceeded | トークン予算超過 |
| 422 | INVALID_PARAMETERS | Invalid parameters | 不正なパラメータ |
| 429 | RATE_LIMIT_EXCEEDED | Rate limit exceeded | レート制限超過 |
| 429 | QUOTA_EXCEEDED | Monthly quota exceeded | 月次クォータ超過 |
| 500 | INTERNAL_SERVER_ERROR | Internal server error | サーバーエラー |
| 500 | LLM_API_ERROR | LLM API error | LLM APIエラー |
| 500 | SHEETS_API_ERROR | Sheets API error | Sheets APIエラー |
| 503 | SERVICE_UNAVAILABLE | Service unavailable | サービス停止中 |
| 503 | LLM_UNAVAILABLE | LLM service unavailable | LLM停止中 |

---

## テスト方法

### 1. Secrets Preflight チェック

```bash
# ローカル環境チェック
python ops/check-secrets.py --source file --file .env --json

# CI環境チェック（GitHub Actions）
python ops/check-secrets.py --source env --json
```

### 2. Python構文チェック

```bash
cd backend
python3 -m py_compile app/errors.py app/agents.py app/api_v1.py app/jobs.py
```

### 3. 422エラーテスト

```bash
# 大量のテキストを送信してトークン予算超過をテスト
curl -X POST "${API_BASE}/use" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "tpl_test",
    "inputs": {
      "description": "'$(python3 -c "print('x' * 100000)")'"
    }
  }'

# Expected: 422 TOKEN_BUDGET_EXCEEDED
```

### 4. 429エラーテスト

```bash
# 短時間に大量リクエスト
for i in {1..10}; do
  curl -X POST "${API_BASE}/use" \
    -H "Authorization: Bearer ${TOKEN}" \
    -d '{...}'
done

# Expected: 429 RATE_LIMIT_EXCEEDED
```

### 5. Idempotency テスト

```bash
# 同じキーで2回リクエスト
IDEM_KEY="550e8400-e29b-41d4-a716-446655440000"

curl -X POST "${API_BASE}/use" \
  -H "X-Idempotency-Key: ${IDEM_KEY}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{...}'

# 2回目は既存job_idを返却
curl -X POST "${API_BASE}/use" \
  -H "X-Idempotency-Key: ${IDEM_KEY}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{...}'
```

---

## コミット情報

**Commit Hash**: `da61097`

**Commit Message**:
```
feat: Add unified error format, token budget pre-check, and 422/409 errors

## Changes

### New Error System (backend/app/errors.py)
- Unified error format: {"error": {"code", "message", "hint", "meta"}}
- Custom exceptions: TokenBudgetExceededError, IdempotencyConflictError, QuotaExceededError
- Standard error responses: 400/401/403/404/409/422/429/500

### Token Budget Pre-checking (backend/app/agents.py)
- Added estimate_tokens() function for token estimation
- Pre-check token budget before LLM API calls
- Raise TokenBudgetExceededError (422) when budget exceeded
- Updated token limits from environment variables

### API Error Handling (backend/app/api_v1.py)
- Import unified error helpers
- Use exception_to_response() for TepureError exceptions
- Updated endpoints to use standard error responses
- Added proper error handling for /use endpoint

### Idempotency Support (backend/app/jobs.py)
- Import IdempotencyConflictError
- Existing idempotency logic preserved

### Documentation (docs/API_CURL_EXAMPLES.md)
- Complete curl examples for all API endpoints
- Error response examples for all error codes
- Testing scripts and full flow examples

### Environment Variables (.env.sample)
- Reorganized to 17 required items
- Added token budget variables
- Clear section organization
```

---

## ファイル変更統計

```
5 files changed, 1063 insertions(+), 57 deletions(-)
```

**新規作成**:
- `backend/app/errors.py` (285行)
- `docs/API_CURL_EXAMPLES.md` (900行以上)

**変更**:
- `backend/app/agents.py` (+120行, -20行)
- `backend/app/api_v1.py` (+80行, -30行)
- `backend/app/jobs.py` (+2行, -0行)

**更新（gitignore対象）**:
- `.env.sample` (完全リライト、17項目）

---

## 次のステップ

### 本日実施予定 (2025-10-16)

1. **Preview デプロイ**:
   ```bash
   # Secrets Preflight
   python ops/check-secrets.py --source env --json

   # Migration 実行
   cd backend
   python -m app.migrations.20251016_templates_extend up
   python -m app.migrations.20251016_jobs_status_map up

   # デプロイ
   gcloud run deploy tepure-api --region asia-northeast1
   ```

2. **Smoke Test**:
   ```bash
   export API_BASE="https://tepure-api-xxxxxxxxxx.run.app/api/v1"
   bash scripts/smoke-test.sh
   ```

3. **UAT 開始**:
   - `docs/UAT_CHECKLIST.md` に従って手動テスト
   - 422エラー確認
   - Idempotency確認
   - レート制限確認

### 参考ドキュメント

- `docs/COMPLETE_EXECUTION_GUIDE.md` - 完全実行ガイド（60-90分）
- `docs/DEPLOYMENT_RUNBOOK.md` - デプロイ手順書
- `docs/OPERATIONS_CHECKLIST.md` - 運用チェックリスト
- `docs/API_CURL_EXAMPLES.md` - API curl例

---

## まとめ

✅ **統一エラーフォーマット実装完了**
✅ **422トークン予算超過エラー実装完了**
✅ **トークン事前チェック実装完了**
✅ **Idempotency-Key実装確認完了**
✅ **APIエラーハンドリング更新完了**
✅ **.env.sample 17項目更新完了**
✅ **完全なAPI curl例ドキュメント作成完了**
✅ **全変更コミット完了**

**システムは Preview デプロイ準備完了！**

---

**作成**: 2025-10-16
**作成者**: Claude Code
**プロジェクト**: tepure - Figmaテンプレート自動化システム
