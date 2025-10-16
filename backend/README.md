# Tepure Backend API

本番運用可能なFlask APIバックエンド for Figma Template Automation

## アーキテクチャ

```
backend/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── schemas.py           # Pydantic models
│   ├── auth.py              # JWT authentication + RBAC
│   ├── sheets.py            # Google Sheets CRUD + audit logs
│   ├── jobs.py              # Job queue + idempotency
│   ├── agents.py            # LLM Agent1/2 integration
│   ├── metrics.py           # Monitoring + audit logs
│   └── api_v1.py            # API routes (Blueprint)
├── tests/
│   ├── conftest.py          # Pytest fixtures
│   └── unit/                # Unit tests
├── requirements.txt         # Python dependencies
├── gunicorn.conf.py         # Production server config
├── Dockerfile               # Container image
├── wsgi.py                  # WSGI entry point
└── mypy.ini                 # Type checking config
```

## 機能

### ✅ 認証・認可
- **BCrypt** パスワードハッシング
- **JWT** トークン認証（Access: 15分, Refresh: 7日）
- **ロールベースアクセス制御** (user/admin)
- PIIマスキング付きログ

### ✅ テンプレート管理
- CRUD操作（GET, POST, PUT, DELETE）
- ページネーション & フィルタリング
- Google Sheetsバックエンド

### ✅ AI生成
- **Agent1**: プロンプト生成
- **Agent2**: JSON構造化
- **Claude Sonnet 4** (Anthropic API)
- トークン制限: 1,500 tokens/job
- コスト計算: 自動追跡

### ✅ ジョブキュー
- In-memoryキュー（将来Cloud Tasksへ移行可能）
- **Idempotencyサポート**
- ステータス追跡: pending → processing → completed/failed

### ✅ 監視・監査
- 構造化ログ（JSON）
- 監査ログ記録（全アクション）
- メトリクス: 成功率、レイテンシ、日次カウント

### ✅ レート制限
- グローバル: 30 req/min
- ユーザー別: 5 req/min (生成エンドポイント)
- 月次クォータ管理

### ✅ 本番環境対応
- **Gunicorn** マルチワーカー
- **Dockerfile** マルチステージビルド
- ヘルスチェック
- 非rootユーザー実行

## セットアップ

### 1. 依存関係インストール

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 環境変数設定

```bash
cp .env.example .env
# .envを編集して以下を設定:
# - JWT_SECRET_KEY
# - GOOGLE_SHEETS_ID
# - GOOGLE_SERVICE_ACCOUNT_JSON (base64エンコード)
# - ANTHROPIC_API_KEY
```

### 3. 開発サーバー起動

```bash
python wsgi.py
# または
flask run --port 8080
```

### 4. 本番サーバー起動（Gunicorn）

```bash
gunicorn -c gunicorn.conf.py wsgi:app
```

### 5. Dockerビルド

```bash
docker build -t tepure-api:latest .
docker run -p 8080:8080 --env-file .env tepure-api:latest
```

## API エンドポイント

### 認証

| Method | Endpoint | 説明 |
|--------|----------|------|
| POST | `/api/v1/auth/login` | ログイン（JWT発行） |
| POST | `/api/v1/auth/refresh` | トークンリフレッシュ |
| POST | `/api/v1/auth/logout` | ログアウト |

### テンプレート

| Method | Endpoint | 説明 | 権限 |
|--------|----------|------|------|
| GET | `/api/v1/templates` | テンプレート一覧 | - |
| GET | `/api/v1/templates/{id}` | テンプレート詳細 | - |
| POST | `/api/v1/templates` | テンプレート作成 | Admin |
| PUT | `/api/v1/templates/{id}` | テンプレート更新 | Admin |
| DELETE | `/api/v1/templates/{id}` | テンプレート削除 | Admin |

### 生成

| Method | Endpoint | 説明 | 権限 |
|--------|----------|------|------|
| POST | `/api/v1/use` | ジョブ作成 | User |
| GET | `/api/v1/jobs/{id}` | ジョブステータス | User |

### 監視（Admin）

| Method | Endpoint | 説明 |
|--------|----------|------|
| GET | `/api/v1/metrics` | システムメトリクス |
| GET | `/api/v1/auditlogs` | 監査ログ |

## テスト

### ユニットテスト

```bash
pytest tests/unit -v
```

### カバレッジ

```bash
pytest --cov=app --cov-report=html tests/
open htmlcov/index.html
```

### 型チェック

```bash
mypy app/
```

## デプロイ

### Cloud Run（推奨）

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/tepure-api

# Deploy
gcloud run deploy tepure-api \
  --image gcr.io/PROJECT_ID/tepure-api \
  --platform managed \
  --region us-central1 \
  --set-env-vars="JWT_SECRET_KEY=xxx,GOOGLE_SHEETS_ID=xxx,..."
```

### Heroku

```bash
heroku create tepure-api
heroku config:set JWT_SECRET_KEY=xxx GOOGLE_SHEETS_ID=xxx ...
git push heroku main
```

## セキュリティ

- ✅ BCryptパスワードハッシング（12 rounds）
- ✅ JWTトークン（短期間有効期限）
- ✅ レート制限（Flask-Limiter）
- ✅ CORS設定
- ✅ PIIマスキング
- ✅ 構造化ログ
- ✅ 非rootユーザー（Docker）

## モニタリング

### ヘルスチェック

```bash
curl http://localhost:8080/health
```

### メトリクス（要Admin権限）

```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8080/api/v1/metrics
```

### ログ

構造化JSON形式でstdoutに出力：

```json
{
  "event": "job_created",
  "timestamp": "2025-10-16T12:00:00Z",
  "level": "info",
  "job_id": "job_123",
  "user_id": "usr_456"
}
```

## パフォーマンス

- **スループット**: ~100 req/s（4 workers）
- **平均レイテンシ**: < 200ms（非LLM）
- **LLM生成**: 2-5秒
- **トークン制限**: 1,500 tokens/job
- **月次コスト**: ~$30（1000 jobs/月想定）

## トラブルシューティング

### Google Sheets接続エラー

```bash
# サービスアカウントJSONを再エンコード
cat service-account.json | base64
# .envのGOOGLE_SERVICE_ACCOUNT_JSONに設定
```

### JWT認証エラー

```bash
# JWT_SECRET_KEYが設定されているか確認
echo $JWT_SECRET_KEY
```

### Anthropic API エラー

```bash
# APIキーが有効か確認
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```

## ライセンス

MIT

---

🌸 Built with Miyabi Framework
