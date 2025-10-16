#!/usr/bin/env bash
#
# Setup GCP Service Account for GitHub Actions
# Usage: bash scripts/setup-gcp-service-account.sh
#

set -euo pipefail

echo "==================================================="
echo "GCP Service Account Setup for GitHub Actions"
echo "==================================================="
echo ""

# Check if GCP_PROJECT_ID is set
if [ -z "${GCP_PROJECT_ID:-}" ]; then
    echo "Please enter your GCP Project ID:"
    read -r GCP_PROJECT_ID
    export GCP_PROJECT_ID
fi

echo "GCP Project ID: $GCP_PROJECT_ID"
echo "Region: asia-northeast1"
echo ""

SA_NAME="github-actions"
SA_EMAIL="${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

# Check if service account exists
echo "Checking if service account exists..."
if gcloud iam service-accounts describe "$SA_EMAIL" --project="$GCP_PROJECT_ID" &>/dev/null; then
    echo "✓ Service account already exists: $SA_EMAIL"
else
    echo "Creating service account: $SA_NAME..."
    gcloud iam service-accounts create "$SA_NAME" \
        --display-name="GitHub Actions Deployer" \
        --description="Service account for GitHub Actions CI/CD" \
        --project="$GCP_PROJECT_ID"
    echo "✅ Service account created"
fi

echo ""
echo "Granting IAM roles..."

# Required roles
ROLES=(
    "roles/run.admin"
    "roles/iam.serviceAccountUser"
    "roles/storage.admin"
    "roles/artifactregistry.writer"
    "roles/secretmanager.secretAccessor"
)

for ROLE in "${ROLES[@]}"; do
    echo "  Granting $ROLE..."
    gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
        --member="serviceAccount:$SA_EMAIL" \
        --role="$ROLE" \
        --condition=None \
        --quiet &>/dev/null || echo "    (already granted or failed)"
done

echo "✅ IAM roles granted"
echo ""

# Create key
KEY_FILE="gcp-sa-key-$(date +%Y%m%d-%H%M%S).json"

echo "Creating service account key..."
gcloud iam service-accounts keys create "$KEY_FILE" \
    --iam-account="$SA_EMAIL" \
    --project="$GCP_PROJECT_ID"

echo "✅ Service account key created: $KEY_FILE"
echo ""

# Display key info
echo "==================================================="
echo "GitHub Secrets Configuration"
echo "==================================================="
echo ""
echo "1. GCP_SA_KEY"
echo "   Copy the entire content of $KEY_FILE:"
echo ""
cat "$KEY_FILE"
echo ""
echo "---------------------------------------------------"
echo ""

# Create base64 version
BASE64_KEY=$(cat "$KEY_FILE" | base64 | tr -d '\n')

echo "2. GOOGLE_SERVICE_ACCOUNT_JSON_BASE64"
echo "   Copy this base64-encoded value:"
echo ""
echo "$BASE64_KEY"
echo ""
echo "---------------------------------------------------"
echo ""

echo "⚠️  IMPORTANT: Store this key securely!"
echo "   - Add to GitHub Secrets: https://github.com/taiyousan15/tepure/settings/secrets/actions"
echo "   - Delete the key file after uploading: rm $KEY_FILE"
echo ""

echo "Next steps:"
echo "1. Open https://github.com/taiyousan15/tepure/settings/secrets/actions"
echo "2. Click 'New repository secret'"
echo "3. Add GCP_SA_KEY (paste entire JSON)"
echo "4. Add GOOGLE_SERVICE_ACCOUNT_JSON_BASE64 (paste base64 string)"
echo "5. Delete the key file: rm $KEY_FILE"
echo ""
echo "Setup complete!"
