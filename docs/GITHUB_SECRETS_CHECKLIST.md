# GitHub Secrets チェックリスト

Preview環境デプロイに必要なGitHub Secretsの一覧です。

**設定ページ**: https://github.com/taiyousan15/tepure/settings/secrets/actions

---

## 必須Secrets (18項目)

### 1. GCP関連 (3項目)

- [ ] **GCP_PROJECT_ID**
  - 説明: Google CloudプロジェクトID
  - 例: `tepure-prod`
  - 取得方法: GCPコンソール → プロジェクト選択 → プロジェクトID

- [ ] **GCP_SA_KEY**
  - 説明: GCPサービスアカウントキー (JSON全体)
  - 形式: JSON文字列
  - 取得方法:
    ```bash
    # サービスアカウント作成
    gcloud iam service-accounts create github-actions \
      --display-name="GitHub Actions"

    # 権限付与
    gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
      --member="serviceAccount:github-actions@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
      --role="roles/run.admin"

    gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
      --member="serviceAccount:github-actions@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
      --role="roles/storage.admin"

    gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
      --member="serviceAccount:github-actions@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
      --role="roles/secretmanager.secretAccessor"

    # キー作成
    gcloud iam service-accounts keys create key.json \
      --iam-account=github-actions@$GCP_PROJECT_ID.iam.gserviceaccount.com

    # key.jsonの内容をGitHub Secretsに登録
    cat key.json
    ```

- [ ] **GOOGLE_SERVICE_ACCOUNT_JSON_BASE64**
  - 説明: Base64エンコードされたGCPサービスアカウントキー
  - 形式: Base64文字列
  - 取得方法:
    ```bash
    cat key.json | base64 | tr -d '\n'
    ```

### 2. Firebase関連 (2項目)

- [ ] **FIREBASE_SERVICE_ACCOUNT**
  - 説明: Firebase Hosting用サービスアカウントキー
  - 取得方法:
    ```bash
    # Firebase CLIでログイン
    firebase login

    # プロジェクトディレクトリで実行
    firebase init hosting

    # サービスアカウントキー取得
    # Firebase Console → Project Settings → Service Accounts → Generate New Private Key
    ```

- [ ] **FIREBASE_PROJECT_ID**
  - 説明: FirebaseプロジェクトID
  - 例: `tepure-hosting`
  - 取得方法: Firebase Console → Project Settings → Project ID

### 3. 認証・API (4項目)

- [ ] **JWT_SECRET**
  - 説明: JWT署名用シークレット
  - 形式: ランダム文字列 (32文字以上推奨)
  - 生成方法:
    ```bash
    openssl rand -base64 32
    ```

- [ ] **REFRESH_SECRET**
  - 説明: リフレッシュトークン用シークレット
  - 形式: ランダム文字列 (32文字以上推奨)
  - 生成方法:
    ```bash
    openssl rand -base64 32
    ```

- [ ] **FIGMA_API_TOKEN**
  - 説明: Figma APIアクセストークン
  - 取得方法: Figma → Settings → Personal Access Tokens → Generate new token

- [ ] **ANTHROPIC_API_KEY** ⭐ **新規追加**
  - 説明: Anthropic Claude APIキー
  - 形式: `sk-ant-xxxxx`
  - 取得方法: https://console.anthropic.com/settings/keys
  - **注意**: 旧名 `LLM_API_KEY` から変更

### 4. Google Sheets (4項目)

- [ ] **SHEETS_USERS_ID**
  - 説明: ユーザー管理用Google Sheets ID
  - 形式: `1ABCdefGHIjklMNOpqrSTUvwxYZ`
  - 取得方法: Google Sheets URL の `/d/` と `/edit` の間の文字列

- [ ] **SHEETS_TEMPLATES_ID**
  - 説明: テンプレート管理用Google Sheets ID

- [ ] **SHEETS_JOBS_ID**
  - 説明: ジョブ管理用Google Sheets ID

- [ ] **SHEETS_AUDITLOGS_ID**
  - 説明: 監査ログ用Google Sheets ID

### 5. オプション (2項目)

- [ ] **SENTRY_DSN** (オプション)
  - 説明: Sentryエラートラッキング用DSN
  - 形式: `https://xxxxx@sentry.io/xxxxx`
  - 取得方法: Sentry → Project Settings → Client Keys (DSN)

- [ ] **GA_MEASUREMENT_ID** (オプション)
  - 説明: Google Analytics測定ID
  - 形式: `G-XXXXXXXXXX`
  - 取得方法: Google Analytics → Admin → Data Streams → Measurement ID

---

## GCP Secret Managerに保存するSecrets

GitHub Actionsから参照されるため、GCP Secret Managerにも以下を保存:

```bash
# 1. JWT_SECRET
echo -n "your-jwt-secret" | gcloud secrets create jwt-secret \
  --data-file=- --project=$GCP_PROJECT_ID

# 2. REFRESH_SECRET
echo -n "your-refresh-secret" | gcloud secrets create refresh-secret \
  --data-file=- --project=$GCP_PROJECT_ID

# 3. GOOGLE_SERVICE_ACCOUNT_JSON_BASE64
echo -n "your-base64-encoded-json" | gcloud secrets create google-sa-json \
  --data-file=- --project=$GCP_PROJECT_ID

# 4. FIGMA_API_TOKEN
echo -n "your-figma-token" | gcloud secrets create figma-token \
  --data-file=- --project=$GCP_PROJECT_ID

# 5. ANTHROPIC_API_KEY ⭐ 新規
echo -n "sk-ant-xxxxx" | gcloud secrets create anthropic-key \
  --data-file=- --project=$GCP_PROJECT_ID

# 6-9. Google Sheets IDs
echo -n "sheet-id-1" | gcloud secrets create sheets-users-id \
  --data-file=- --project=$GCP_PROJECT_ID

echo -n "sheet-id-2" | gcloud secrets create sheets-templates-id \
  --data-file=- --project=$GCP_PROJECT_ID

echo -n "sheet-id-3" | gcloud secrets create sheets-jobs-id \
  --data-file=- --project=$GCP_PROJECT_ID

echo -n "sheet-id-4" | gcloud secrets create sheets-auditlogs-id \
  --data-file=- --project=$GCP_PROJECT_ID
```

---

## Secrets設定後の確認

### GitHub Secrets確認
```bash
gh secret list -R taiyousan15/tepure
```

### GCP Secret Manager確認
```bash
gcloud secrets list --project=$GCP_PROJECT_ID
```

### ワークフロー実行
```bash
# GitHub Actions画面で手動実行
# https://github.com/taiyousan15/tepure/actions/workflows/preview-deploy.yml
```

---

## トラブルシューティング

### Secret Managerアクセスエラー
```bash
# サービスアカウントに権限追加
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:github-actions@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Cloud Run デプロイエラー
```bash
# サービスアカウントに権限追加
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:github-actions@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:github-actions@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

### Artifact Registry プッシュエラー
```bash
# Artifact Registry作成
gcloud artifacts repositories create tepure \
  --repository-format=docker \
  --location=asia-northeast1 \
  --project=$GCP_PROJECT_ID

# サービスアカウントに権限追加
gcloud artifacts repositories add-iam-policy-binding tepure \
  --location=asia-northeast1 \
  --member="serviceAccount:github-actions@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer" \
  --project=$GCP_PROJECT_ID
```

---

**更新日**: 2025-10-16
**対象**: Preview環境デプロイ
