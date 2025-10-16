# Database Migrations

このディレクトリには、Google Sheets データベースのスキーマ変更を行うマイグレーションスクリプトが含まれています。

## 📋 Available Migrations

### 20251016_templates_extend.py

**目的**: Templates スキーマを拡張

**追加カラム**:
- `category`: LP/Banner/SNS/WebApp (Literal型)
- `fields`: JSON配列（Field[]）
- `figma_node_id`: FigmaノードID
- `preview_url`: プレビュー画像URL

**実行方法**:
```bash
cd backend
source venv/bin/activate
export $(cat ../.env | grep -v '^#' | xargs)
python -m app.migrations.20251016_templates_extend
```

**ロールバック**:
```bash
python -m app.migrations.20251016_templates_extend down
```

### 20251016_jobs_status_map.py

**目的**: Jobs ステータス語彙を標準化

**変換内容**:
- `queued` → `pending`
- `running` → `processing`
- `succeeded` → `completed`
- `failed` → `failed` (変更なし)

**実行方法**:
```bash
cd backend
source venv/bin/activate
export $(cat ../.env | grep -v '^#' | xargs)
python -m app.migrations.20251016_jobs_status_map
```

**ロールバック**:
```bash
python -m app.migrations.20251016_jobs_status_map down
```

---

## 🚀 実行手順

### 前提条件

1. **Google Sheets バックアップ必須**
   - Users シート
   - Templates シート
   - Jobs シート
   - AuditLogs シート

2. **環境変数設定**
   ```bash
   GOOGLE_SERVICE_ACCOUNT_JSON_BASE64=<base64-encoded-json>
   SHEETS_USERS_ID=<spreadsheet-id>
   SHEETS_TEMPLATES_ID=<spreadsheet-id>
   SHEETS_JOBS_ID=<spreadsheet-id>
   SHEETS_AUDITLOGS_ID=<spreadsheet-id>
   ```

### 実行順序（推奨）

```bash
# 1. バックアップ確認
echo "バックアップを取得しましたか？ [y/N]"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
  echo "まずバックアップを取得してください"
  exit 1
fi

# 2. Templates スキーマ拡張
python -m app.migrations.20251016_templates_extend

# 3. 結果確認
# 期待: {"status": "completed", "updated_rows": N}

# 4. Jobs ステータス変換
python -m app.migrations.20251016_jobs_status_map

# 5. 結果確認
# 期待: {"status": "completed", "updated_rows": N}

# 6. 手動データ更新
# Google Sheets で category, fields, preview_url, figma_node_id を設定
```

---

## 📊 実行結果の確認

### 成功時のレスポンス例

#### templates_extend

```json
{
  "migration": "20251016_templates_extend",
  "status": "completed",
  "total_rows": 30,
  "updated_rows": 30,
  "new_columns": ["category", "preview_url", "fields", "figma_node_id"],
  "message": "Migration completed. Please update category, preview_url, fields, and figma_node_id manually."
}
```

#### jobs_status_map

```json
{
  "migration": "20251016_jobs_status_map",
  "status": "completed",
  "total_rows": 150,
  "updated_rows": 120,
  "errors": [],
  "error_count": 0
}
```

### 失敗時の対応

**エラー例**:
```json
{
  "migration": "20251016_templates_extend",
  "status": "failed",
  "error": "Rate limit exceeded"
}
```

**対応**:
1. Google Sheets API レート制限の場合: 数分待機後に再実行
2. 権限エラーの場合: Service Account に Editor 権限を付与
3. その他のエラー: ログを確認し、手動で修正

---

## 🔄 ロールバック

### いつロールバックするか

- マイグレーション実行中にエラーが発生
- 本番環境で予期しない動作が発生
- UAT で重大な不具合が発見

### ロールバック手順

```bash
# 1. Templates ロールバック
python -m app.migrations.20251016_templates_extend down

# 2. Jobs ロールバック
python -m app.migrations.20251016_jobs_status_map down

# 3. バックアップから復元（最終手段）
# Google Sheets の「ファイル」→「バージョン履歴」→「以前のバージョンを復元」
```

**警告**: ロールバックすると、新規カラムのデータは失われます。

---

## 📝 手動データ更新

### Templates シート

マイグレーション後、以下のカラムを手動で設定してください：

#### category 設定

| テンプレート名 | category |
|---------------|----------|
| ランディングページ | LP |
| バナー広告 | Banner |
| Instagram投稿 | SNS |
| Webアプリ画面 | WebApp |

#### fields 設定

**JSON形式例**:
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

**設定手順**:
1. Google Sheets で Templates シートを開く
2. `fields` カラムを見つける
3. 各行にJSON配列を貼り付け

#### preview_url 設定

Figma ファイルのプレビュー画像URLを設定：
```
https://s3.us-west-2.amazonaws.com/figma-alpha-api/img/...
```

#### figma_node_id 設定

Figmaのノードパスを設定：
```
1:234
2:345
```

---

## 🧪 テスト

### ローカル実行テスト

```bash
# テスト用環境変数（サンプルスプレッドシート）
export SHEETS_TEMPLATES_ID="test-spreadsheet-id"
export SHEETS_JOBS_ID="test-spreadsheet-id"

# マイグレーション実行
python -m app.migrations.20251016_templates_extend
python -m app.migrations.20251016_jobs_status_map

# ロールバック
python -m app.migrations.20251016_templates_extend down
python -m app.migrations.20251016_jobs_status_map down
```

### CI/CD 統合

マイグレーションはデプロイ前に自動実行されません。
**手動実行を推奨**します。理由：
- データベース変更は慎重に行うべき
- ロールバックが必要な場合がある
- 本番環境へのデプロイ前に Preview で確認

---

## 📚 参考ドキュメント

- [MIGRATION_GUIDE.md](../../../docs/MIGRATION_GUIDE.md) - 完全な移行手順
- [DEPLOYMENT_RUNBOOK.md](../../../docs/DEPLOYMENT_RUNBOOK.md) - デプロイ手順
- [DIFFERENTIAL_UPDATE_SUMMARY.md](../../../docs/DIFFERENTIAL_UPDATE_SUMMARY.md) - 実装サマリー

---

## ❓ FAQ

### Q: マイグレーションは本番環境で実行しても安全ですか？

A: はい、以下の条件を満たす場合：
- ✅ バックアップを取得済み
- ✅ Preview 環境でテスト済み
- ✅ UAT で問題なし
- ✅ ロールバック手順を理解している

### Q: マイグレーション中にAPIを停止する必要がありますか？

A: いいえ、マイグレーションは additive changes のみなので、API稼働中でも実行可能です。

### Q: エラーが発生した場合は？

A: 以下の順で対応：
1. エラーメッセージを確認
2. Google Sheets API レート制限の場合は待機後に再実行
3. ロールバックを実行
4. バックアップから復元（最終手段）

### Q: 手動データ更新をスキップできますか？

A: デフォルト値が設定されますが、以下は必ず更新推奨：
- category: デフォルト "LP"
- fields: デフォルト空配列
- preview_url: デフォルト空文字列
- figma_node_id: デフォルト空文字列

---

**実施前に必ずバックアップを取得してください。**
