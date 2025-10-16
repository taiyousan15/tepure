#!/usr/bin/env bash
#
# Setup All Secrets for Preview Deployment
# Usage: bash scripts/setup-all-secrets.sh
#

set -euo pipefail

echo "==================================================="
echo "Complete Secrets Setup for tepure Preview Deploy"
echo "==================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check dependencies
echo "Checking dependencies..."
MISSING_DEPS=()

if ! command -v gcloud &>/dev/null; then
    MISSING_DEPS+=("gcloud")
fi

if ! command -v gh &>/dev/null; then
    MISSING_DEPS+=("gh")
fi

if ! command -v openssl &>/dev/null; then
    MISSING_DEPS+=("openssl")
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo -e "${RED}❌ Missing dependencies: ${MISSING_DEPS[*]}${NC}"
    echo ""
    echo "Install with:"
    for dep in "${MISSING_DEPS[@]}"; do
        case $dep in
            gcloud)
                echo "  brew install --cask google-cloud-sdk"
                ;;
            gh)
                echo "  brew install gh"
                ;;
            openssl)
                echo "  brew install openssl"
                ;;
        esac
    done
    exit 1
fi

echo -e "${GREEN}✓ All dependencies installed${NC}"
echo ""

# Get GCP Project ID
if [ -z "${GCP_PROJECT_ID:-}" ]; then
    echo "Enter your GCP Project ID:"
    read -r GCP_PROJECT_ID
    export GCP_PROJECT_ID
fi

echo "GCP Project ID: $GCP_PROJECT_ID"
echo ""

# Verify GCP authentication
echo "Verifying GCP authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &>/dev/null; then
    echo -e "${YELLOW}⚠️  Not authenticated to GCP${NC}"
    echo "Run: gcloud auth login"
    exit 1
fi
echo -e "${GREEN}✓ GCP authenticated${NC}"
echo ""

# Verify GitHub authentication
echo "Verifying GitHub authentication..."
if ! gh auth status &>/dev/null; then
    echo -e "${YELLOW}⚠️  Not authenticated to GitHub${NC}"
    echo "Run: gh auth login"
    exit 1
fi
echo -e "${GREEN}✓ GitHub authenticated${NC}"
echo ""

# Create temporary directory for secrets
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo "==================================================="
echo "Step 1: Generate JWT Secrets"
echo "==================================================="
echo ""

JWT_SECRET=$(openssl rand -base64 32)
REFRESH_SECRET=$(openssl rand -base64 32)

echo -e "${GREEN}✓ JWT_SECRET generated${NC}"
echo -e "${GREEN}✓ REFRESH_SECRET generated${NC}"
echo ""

# Save to GCP Secret Manager
echo "Adding to GCP Secret Manager..."
echo -n "$JWT_SECRET" | gcloud secrets create jwt-secret \
    --data-file=- --replication-policy="automatic" --project="$GCP_PROJECT_ID" 2>/dev/null || \
echo -n "$JWT_SECRET" | gcloud secrets versions add jwt-secret \
    --data-file=- --project="$GCP_PROJECT_ID"

echo -n "$REFRESH_SECRET" | gcloud secrets create refresh-secret \
    --data-file=- --replication-policy="automatic" --project="$GCP_PROJECT_ID" 2>/dev/null || \
echo -n "$REFRESH_SECRET" | gcloud secrets versions add refresh-secret \
    --data-file=- --project="$GCP_PROJECT_ID"

echo -e "${GREEN}✓ JWT secrets added to Secret Manager${NC}"
echo ""

echo "==================================================="
echo "Step 2: Prompt for API Keys"
echo "==================================================="
echo ""

# Anthropic API Key
echo "Enter your Anthropic API Key (sk-ant-...):"
read -s ANTHROPIC_API_KEY
echo ""

if [[ ! "$ANTHROPIC_API_KEY" =~ ^sk-ant- ]]; then
    echo -e "${YELLOW}⚠️  Warning: API key doesn't start with 'sk-ant-'${NC}"
fi

echo -n "$ANTHROPIC_API_KEY" | gcloud secrets create anthropic-key \
    --data-file=- --replication-policy="automatic" --project="$GCP_PROJECT_ID" 2>/dev/null || \
echo -n "$ANTHROPIC_API_KEY" | gcloud secrets versions add anthropic-key \
    --data-file=- --project="$GCP_PROJECT_ID"

echo -e "${GREEN}✓ ANTHROPIC_API_KEY added to Secret Manager${NC}"
echo ""

# Figma API Token
echo "Enter your Figma API Token (figd_...):"
read -s FIGMA_API_TOKEN
echo ""

echo -n "$FIGMA_API_TOKEN" | gcloud secrets create figma-token \
    --data-file=- --replication-policy="automatic" --project="$GCP_PROJECT_ID" 2>/dev/null || \
echo -n "$FIGMA_API_TOKEN" | gcloud secrets versions add figma-token \
    --data-file=- --project="$GCP_PROJECT_ID"

echo -e "${GREEN}✓ FIGMA_API_TOKEN added to Secret Manager${NC}"
echo ""

echo "==================================================="
echo "Step 3: Google Sheets IDs"
echo "==================================================="
echo ""

echo "Enter SHEETS_USERS_ID (Google Sheets ID):"
read -r SHEETS_USERS_ID
echo -n "$SHEETS_USERS_ID" | gcloud secrets create sheets-users-id \
    --data-file=- --replication-policy="automatic" --project="$GCP_PROJECT_ID" 2>/dev/null || \
echo -n "$SHEETS_USERS_ID" | gcloud secrets versions add sheets-users-id \
    --data-file=- --project="$GCP_PROJECT_ID"

echo "Enter SHEETS_TEMPLATES_ID:"
read -r SHEETS_TEMPLATES_ID
echo -n "$SHEETS_TEMPLATES_ID" | gcloud secrets create sheets-templates-id \
    --data-file=- --replication-policy="automatic" --project="$GCP_PROJECT_ID" 2>/dev/null || \
echo -n "$SHEETS_TEMPLATES_ID" | gcloud secrets versions add sheets-templates-id \
    --data-file=- --project="$GCP_PROJECT_ID"

echo "Enter SHEETS_JOBS_ID:"
read -r SHEETS_JOBS_ID
echo -n "$SHEETS_JOBS_ID" | gcloud secrets create sheets-jobs-id \
    --data-file=- --replication-policy="automatic" --project="$GCP_PROJECT_ID" 2>/dev/null || \
echo -n "$SHEETS_JOBS_ID" | gcloud secrets versions add sheets-jobs-id \
    --data-file=- --project="$GCP_PROJECT_ID"

echo "Enter SHEETS_AUDITLOGS_ID:"
read -r SHEETS_AUDITLOGS_ID
echo -n "$SHEETS_AUDITLOGS_ID" | gcloud secrets create sheets-auditlogs-id \
    --data-file=- --replication-policy="automatic" --project="$GCP_PROJECT_ID" 2>/dev/null || \
echo -n "$SHEETS_AUDITLOGS_ID" | gcloud secrets versions add sheets-auditlogs-id \
    --data-file=- --project="$GCP_PROJECT_ID"

echo -e "${GREEN}✓ All Google Sheets IDs added to Secret Manager${NC}"
echo ""

echo "==================================================="
echo "Step 4: GCP Service Account"
echo "==================================================="
echo ""

SA_NAME="github-actions"
SA_EMAIL="${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

# Check if service account exists
if ! gcloud iam service-accounts describe "$SA_EMAIL" --project="$GCP_PROJECT_ID" &>/dev/null; then
    echo "Creating service account..."
    gcloud iam service-accounts create "$SA_NAME" \
        --display-name="GitHub Actions" \
        --project="$GCP_PROJECT_ID"
    echo -e "${GREEN}✓ Service account created${NC}"
else
    echo -e "${GREEN}✓ Service account already exists${NC}"
fi

# Grant roles
ROLES=(
    "roles/run.admin"
    "roles/iam.serviceAccountUser"
    "roles/storage.admin"
    "roles/artifactregistry.writer"
    "roles/secretmanager.secretAccessor"
)

for ROLE in "${ROLES[@]}"; do
    gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
        --member="serviceAccount:$SA_EMAIL" \
        --role="$ROLE" \
        --condition=None \
        --quiet &>/dev/null || true
done

echo -e "${GREEN}✓ IAM roles granted${NC}"
echo ""

# Create key
KEY_FILE="$TEMP_DIR/gcp-sa-key.json"
gcloud iam service-accounts keys create "$KEY_FILE" \
    --iam-account="$SA_EMAIL" \
    --project="$GCP_PROJECT_ID"

GCP_SA_KEY=$(cat "$KEY_FILE")
GOOGLE_SA_BASE64=$(cat "$KEY_FILE" | base64 | tr -d '\n')

echo -e "${GREEN}✓ Service account key created${NC}"
echo ""

echo "==================================================="
echo "Step 5: Firebase Configuration"
echo "==================================================="
echo ""

echo "Enter your Firebase Project ID:"
read -r FIREBASE_PROJECT_ID

echo ""
echo "Firebase Service Account setup:"
echo "1. Go to: https://console.firebase.google.com/project/$FIREBASE_PROJECT_ID/settings/serviceaccounts/adminsdk"
echo "2. Click 'Generate new private key'"
echo "3. Save the JSON file"
echo ""
echo "Press Enter when ready to continue..."
read -r

echo "Enter path to Firebase service account JSON file:"
read -r FIREBASE_SA_PATH

if [ ! -f "$FIREBASE_SA_PATH" ]; then
    echo -e "${RED}❌ File not found: $FIREBASE_SA_PATH${NC}"
    exit 1
fi

FIREBASE_SERVICE_ACCOUNT=$(cat "$FIREBASE_SA_PATH")

echo -e "${GREEN}✓ Firebase service account loaded${NC}"
echo ""

echo "==================================================="
echo "Step 6: Adding Secrets to GitHub"
echo "==================================================="
echo ""

# Add secrets to GitHub
gh secret set GCP_PROJECT_ID --body "$GCP_PROJECT_ID" --repo taiyousan15/tepure
gh secret set GCP_SA_KEY --body "$GCP_SA_KEY" --repo taiyousan15/tepure
gh secret set GOOGLE_SERVICE_ACCOUNT_JSON_BASE64 --body "$GOOGLE_SA_BASE64" --repo taiyousan15/tepure
gh secret set JWT_SECRET --body "$JWT_SECRET" --repo taiyousan15/tepure
gh secret set REFRESH_SECRET --body "$REFRESH_SECRET" --repo taiyousan15/tepure
gh secret set ANTHROPIC_API_KEY --body "$ANTHROPIC_API_KEY" --repo taiyousan15/tepure
gh secret set FIGMA_API_TOKEN --body "$FIGMA_API_TOKEN" --repo taiyousan15/tepure
gh secret set SHEETS_USERS_ID --body "$SHEETS_USERS_ID" --repo taiyousan15/tepure
gh secret set SHEETS_TEMPLATES_ID --body "$SHEETS_TEMPLATES_ID" --repo taiyousan15/tepure
gh secret set SHEETS_JOBS_ID --body "$SHEETS_JOBS_ID" --repo taiyousan15/tepure
gh secret set SHEETS_AUDITLOGS_ID --body "$SHEETS_AUDITLOGS_ID" --repo taiyousan15/tepure
gh secret set FIREBASE_PROJECT_ID --body "$FIREBASE_PROJECT_ID" --repo taiyousan15/tepure
gh secret set FIREBASE_SERVICE_ACCOUNT --body "$FIREBASE_SERVICE_ACCOUNT" --repo taiyousan15/tepure

echo -e "${GREEN}✓ All secrets added to GitHub${NC}"
echo ""

echo "==================================================="
echo "✅ Setup Complete!"
echo "==================================================="
echo ""
echo "Summary:"
echo "  - GCP Secret Manager: 9 secrets"
echo "  - GitHub Secrets: 13 secrets"
echo "  - Service Account: $SA_EMAIL"
echo ""
echo "Next steps:"
echo "1. Run Preview deployment workflow:"
echo "   gh workflow run preview-deploy.yml --repo taiyousan15/tepure"
echo ""
echo "2. Monitor workflow:"
echo "   https://github.com/taiyousan15/tepure/actions"
echo ""
echo "3. View deployment summary when complete"
echo ""
