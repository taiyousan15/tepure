# Secrets設定ガイド - Preview環境デプロイ

このガイドでは、Preview環境デプロイに必要なすべてのSecretsを設定する方法を説明します。

---

## 🚀 クイックスタート (推奨)

### 方法1: 自動セットアップスクリプト (最も簡単)

すべてのSecretsを一度に設定:

```bash
# 前提条件確認
gcloud --version  # Google Cloud SDK
gh --version      # GitHub CLI
openssl version   # OpenSSL

# まだインストールしていない場合
brew install --cask google-cloud-sdk
brew install gh
brew install openssl

# 認証
gcloud auth login
gh auth login

# 一括セットアップ実行
bash scripts/setup-all-secrets.sh
```

このスクリプトは以下を自動実行します:
- JWT/Refresh Token生成
- GCPサービスアカウント作成
- GCP Secret Manager設定
- GitHub Secrets設定

**所要時間**: 約10-15分

---

## 📋 方法2: 手動セットアップ (段階的)

### Step 1: GCPプロジェクト設定

```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="asia-northeast1"
```

### Step 2: GCPサービスアカウント作成

```bash
bash scripts/setup-gcp-service-account.sh
```

出力されたJSONをコピーして:
1. GitHub Secrets → `GCP_SA_KEY` に貼り付け
2. Base64版を `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` に貼り付け

### Step 3: JWT Secrets生成

```bash
bash scripts/generate-jwt-secrets.sh
```

出力された値を:
1. `JWT_SECRET` → GitHub Secretsに追加
2. `REFRESH_SECRET` → GitHub Secretsに追加

### Step 4: Anthropic API Key設定

```bash
bash scripts/setup-anthropic-secret.sh
```

または手動で:
1. https://console.anthropic.com/settings/keys にアクセス
2. "Create Key" をクリック
3. キーをコピー (`sk-ant-xxxxx`)
4. GitHub Secrets → `ANTHROPIC_API_KEY` に追加

### Step 5: Figma API Token

1. https://www.figma.com/settings にアクセス
2. "Personal Access Tokens" セクション
3. "Generate new token" をクリック
4. トークンをコピー
5. GitHub Secrets → `FIGMA_API_TOKEN` に追加

### Step 6: Google Sheets IDs

各SheetのURLから ID を抽出:
```
https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit
                                      ^^^^^^^^^^^^
```

GitHub Secretsに追加:
- `SHEETS_USERS_ID`
- `SHEETS_TEMPLATES_ID`
- `SHEETS_JOBS_ID`
- `SHEETS_AUDITLOGS_ID`

### Step 7: Firebase設定

1. Firebase Console: https://console.firebase.google.com/
2. プロジェクト選択
3. Project Settings → Service Accounts
4. "Generate new private key" をクリック
5. JSONファイルをダウンロード
6. GitHub Secretsに追加:
   - `FIREBASE_PROJECT_ID`: プロジェクトID
   - `FIREBASE_SERVICE_ACCOUNT`: JSONファイルの内容全体

### Step 8: GCP Project ID

GitHub Secretsに追加:
- `GCP_PROJECT_ID`: GCPプロジェクトID

---

## ✅ 設定完了チェックリスト

### GitHub Secretsに設定済みか確認:

```bash
gh secret list --repo taiyousan15/tepure
```

必要なSecrets (13項目):
- [ ] `GCP_PROJECT_ID`
- [ ] `GCP_SA_KEY`
- [ ] `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64`
- [ ] `JWT_SECRET`
- [ ] `REFRESH_SECRET`
- [ ] `ANTHROPIC_API_KEY` ⭐
- [ ] `FIGMA_API_TOKEN`
- [ ] `SHEETS_USERS_ID`
- [ ] `SHEETS_TEMPLATES_ID`
- [ ] `SHEETS_JOBS_ID`
- [ ] `SHEETS_AUDITLOGS_ID`
- [ ] `FIREBASE_PROJECT_ID`
- [ ] `FIREBASE_SERVICE_ACCOUNT`

### GCP Secret Managerに設定済みか確認:

```bash
gcloud secrets list --project=$GCP_PROJECT_ID
```

必要なSecrets (9項目):
- [ ] `jwt-secret`
- [ ] `refresh-secret`
- [ ] `google-sa-json`
- [ ] `figma-token`
- [ ] `anthropic-key` ⭐
- [ ] `sheets-users-id`
- [ ] `sheets-templates-id`
- [ ] `sheets-jobs-id`
- [ ] `sheets-auditlogs-id`

---

## 🎯 設定後: ワークフロー実行

### GitHub Web UIから:

1. https://github.com/taiyousan15/tepure/actions/workflows/preview-deploy.yml
2. "Run workflow" をクリック
3. Branch: `main` を選択
4. (オプション) Image tag を指定
5. "Run workflow" を実行

### GitHub CLIから:

```bash
gh workflow run preview-deploy.yml --repo taiyousan15/tepure
```

### 実行状況確認:

```bash
# 最新のワークフロー実行を表示
gh run list --repo taiyousan15/tepure --workflow=preview-deploy.yml --limit 1

# ログをリアルタイムで表示
gh run watch --repo taiyousan15/tepure
```

---

## 🔧 トラブルシューティング

### Secret Managerアクセスエラー

```bash
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:github-actions@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Cloud Run デプロイエラー

```bash
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:github-actions@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"
```

### Artifact Registry エラー

```bash
# リポジトリ作成
gcloud artifacts repositories create tepure \
  --repository-format=docker \
  --location=asia-northeast1 \
  --project=$GCP_PROJECT_ID

# 権限付与
gcloud artifacts repositories add-iam-policy-binding tepure \
  --location=asia-northeast1 \
  --member="serviceAccount:github-actions@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer" \
  --project=$GCP_PROJECT_ID
```

### Firebase Deploy エラー

```bash
# Firebase CLI でログイン
firebase login

# プロジェクト設定確認
firebase projects:list

# Hosting設定
cd frontend
firebase init hosting
```

---

## 📚 参考資料

- [GitHub Secrets設定チェックリスト](./GITHUB_SECRETS_CHECKLIST.md)
- [実行ガイド差分](./EXECUTION_GUIDE_DIFF_20251016.md)
- [完全実行ガイド](./COMPLETE_EXECUTION_GUIDE.md)

---

**更新日**: 2025-10-16
**対象**: Preview環境デプロイ
