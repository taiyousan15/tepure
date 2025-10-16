#!/usr/bin/env bash
#
# Setup Anthropic API Key in GCP Secret Manager
# Usage: bash scripts/setup-anthropic-secret.sh
#

set -euo pipefail

echo "==================================================="
echo "Anthropic API Key Setup for GCP Secret Manager"
echo "==================================================="
echo ""

# Check if GCP_PROJECT_ID is set
if [ -z "${GCP_PROJECT_ID:-}" ]; then
    echo "❌ GCP_PROJECT_ID environment variable is not set"
    echo ""
    echo "Please run:"
    echo "  export GCP_PROJECT_ID=your-project-id"
    exit 1
fi

echo "GCP Project ID: $GCP_PROJECT_ID"
echo ""

# Prompt for Anthropic API Key
echo "Please enter your Anthropic API Key (starts with sk-ant-):"
read -s ANTHROPIC_API_KEY

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ No API key provided"
    exit 1
fi

if [[ ! "$ANTHROPIC_API_KEY" =~ ^sk-ant- ]]; then
    echo "⚠️  Warning: API key doesn't start with 'sk-ant-'. Are you sure this is correct?"
    echo "Continue anyway? (y/N)"
    read -r CONFIRM
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        echo "Aborted"
        exit 1
    fi
fi

echo ""
echo "Checking if 'anthropic-key' secret exists..."

# Check if secret exists
if gcloud secrets describe anthropic-key --project="$GCP_PROJECT_ID" &>/dev/null; then
    echo "✓ Secret 'anthropic-key' exists"
    echo ""
    echo "Do you want to add a new version? (y/N)"
    read -r ADD_VERSION

    if [[ "$ADD_VERSION" =~ ^[Yy]$ ]]; then
        echo "Adding new version to 'anthropic-key'..."
        echo -n "$ANTHROPIC_API_KEY" | gcloud secrets versions add anthropic-key \
            --data-file=- \
            --project="$GCP_PROJECT_ID"
        echo "✅ New version added to 'anthropic-key'"
    else
        echo "Skipping version add"
    fi
else
    echo "Creating new secret 'anthropic-key'..."
    echo -n "$ANTHROPIC_API_KEY" | gcloud secrets create anthropic-key \
        --data-file=- \
        --replication-policy="automatic" \
        --project="$GCP_PROJECT_ID"
    echo "✅ Secret 'anthropic-key' created"
fi

echo ""
echo "Verifying secret..."
VERSION=$(gcloud secrets versions list anthropic-key \
    --project="$GCP_PROJECT_ID" \
    --limit=1 \
    --format="value(name)")

if [ -n "$VERSION" ]; then
    echo "✅ Latest version: $VERSION"
    echo ""
    echo "Secret 'anthropic-key' is ready to use!"
    echo ""
    echo "Next steps:"
    echo "1. Add ANTHROPIC_API_KEY to GitHub Secrets"
    echo "   https://github.com/taiyousan15/tepure/settings/secrets/actions"
    echo ""
    echo "2. Grant access to Cloud Run service account:"
    echo "   gcloud secrets add-iam-policy-binding anthropic-key \\"
    echo "     --member='serviceAccount:YOUR-SERVICE-ACCOUNT@$GCP_PROJECT_ID.iam.gserviceaccount.com' \\"
    echo "     --role='roles/secretmanager.secretAccessor' \\"
    echo "     --project='$GCP_PROJECT_ID'"
else
    echo "❌ Failed to verify secret"
    exit 1
fi
