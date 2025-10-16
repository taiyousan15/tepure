# 🚀 Quick Start - Tepure Backend API

本番運用可能なFlask APIの即座起動ガイド

## ⚡ 3ステップで起動

### 1. 依存関係インストール

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 環境変数設定

```bash
cp .env.example .env
```

`.env` を編集：

```bash
JWT_SECRET_KEY=your-secret-key-here
GOOGLE_SHEETS_ID=your-sheets-id
GOOGLE_SERVICE_ACCOUNT_JSON=base64-encoded-json
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

### 3. サーバー起動

```bash
# 開発モード
python wsgi.py

# 本番モード（Gunicorn）
gunicorn -c gunicorn.conf.py wsgi:app
```

サーバーが起動: **http://localhost:8080**

## 🧪 動作確認

### ヘルスチェック

```bash
curl http://localhost:8080/health
```

期待するレスポンス:
```json
{
  "status": "healthy",
  "service": "tepure-api",
  "version": "1.0.0"
}
```

### テスト実行

```bash
# ユニットテスト
pytest tests/unit -v

# カバレッジ付き
pytest --cov=app tests/unit
```

期待: **24 tests passed, 80%+ coverage**

## 📚 API エンドポイント

### 認証

```bash
# ログイン
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

### テンプレート一覧

```bash
curl http://localhost:8080/api/v1/templates
```

### ジョブ作成（要認証）

```bash
curl -X POST http://localhost:8080/api/v1/use \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "template_id": "tpl_123",
    "inputs": {"title": "Hello", "description": "World"},
    "temperature": 0.7,
    "intensity": "medium"
  }'
```

## 🐳 Docker起動

```bash
# ビルド
docker build -t tepure-api:latest .

# 実行
docker run -p 8080:8080 --env-file .env tepure-api:latest
```

## 🛠️ Makefile コマンド

```bash
make install      # 依存関係インストール
make test         # テスト実行
make coverage     # カバレッジレポート
make typecheck    # 型チェック
make run          # 開発サーバー起動
make prod         # 本番サーバー起動
make docker-build # Dockerビルド
```

## 📊 システム構成

### 主要コンポーネント

| ファイル | 役割 |
|---------|------|
| `app/__init__.py` | Flask app factory |
| `app/schemas.py` | Pydantic models (11 schemas) |
| `app/auth.py` | BCrypt + JWT + RBAC |
| `app/sheets.py` | Google Sheets CRUD |
| `app/jobs.py` | Job queue + idempotency |
| `app/agents.py` | LLM Agent1/2 (Claude Sonnet 4) |
| `app/metrics.py` | メトリクス・監査ログ |
| `app/api_v1.py` | REST API (14 endpoints) |

### テスト

| ファイル | テスト数 |
|---------|---------|
| `tests/unit/test_auth.py` | 8 tests |
| `tests/unit/test_jobs.py` | 6 tests |
| `tests/unit/test_schemas.py` | 10 tests |

**合計**: **24 tests**

## 🔐 セキュリティ設定

### 環境変数（必須）

```bash
JWT_SECRET_KEY=xxxxx          # JWT署名キー（強力なランダム文字列）
GOOGLE_SHEETS_ID=xxxxx        # Google SheetsのID
GOOGLE_SERVICE_ACCOUNT_JSON=xxxxx  # base64エンコードされたJSON
ANTHROPIC_API_KEY=sk-ant-xxxxx     # Anthropic API Key
```

### Base64エンコード方法

```bash
# サービスアカウントJSONをエンコード
cat service-account.json | base64 | tr -d '\n'
```

## 📖 詳細ドキュメント

- **README.md** - 包括的ドキュメント
- **IMPLEMENTATION_SUMMARY.md** - 実装詳細
- **TESTING_GUIDE.md** - テストガイド

## ❓ トラブルシューティング

### 問題1: `ModuleNotFoundError`

```bash
# 仮想環境が有効か確認
which python
# → venv/bin/python であること

# 依存関係再インストール
pip install -r requirements.txt
```

### 問題2: Google Sheets接続エラー

```bash
# 環境変数確認
echo $GOOGLE_SHEETS_ID
echo $GOOGLE_SERVICE_ACCOUNT_JSON | base64 -d | jq .

# サービスアカウントに以下の権限が必要:
# - Sheets API有効化
# - スプレッドシートへの編集権限
```

### 問題3: JWT認証エラー

```bash
# JWT_SECRET_KEYが設定されているか確認
echo $JWT_SECRET_KEY

# 強力なキーを生成
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 🎯 次のステップ

1. ✅ 環境変数設定
2. ✅ サーバー起動確認
3. ✅ ヘルスチェック
4. ✅ テスト実行
5. ✅ API動作確認
6. ✅ デプロイ（Cloud Run / Heroku）

## 📞 サポート

- **README.md** - 詳細ドキュメント
- **GitHub Issues** - バグ報告・機能要望

---

🌸 **Miyabi Framework** - Ready for Production!
