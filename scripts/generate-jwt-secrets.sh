#!/usr/bin/env bash
#
# Generate JWT and Refresh Token Secrets
# Usage: bash scripts/generate-jwt-secrets.sh
#

set -euo pipefail

echo "==================================================="
echo "JWT & Refresh Token Secret Generation"
echo "==================================================="
echo ""

# Generate JWT_SECRET
echo "Generating JWT_SECRET (32 bytes)..."
JWT_SECRET=$(openssl rand -base64 32)
echo "✅ JWT_SECRET generated"
echo ""

# Generate REFRESH_SECRET
echo "Generating REFRESH_SECRET (32 bytes)..."
REFRESH_SECRET=$(openssl rand -base64 32)
echo "✅ REFRESH_SECRET generated"
echo ""

echo "==================================================="
echo "GitHub Secrets Configuration"
echo "==================================================="
echo ""

echo "1. JWT_SECRET"
echo "---------------------------------------------------"
echo "$JWT_SECRET"
echo "---------------------------------------------------"
echo ""

echo "2. REFRESH_SECRET"
echo "---------------------------------------------------"
echo "$REFRESH_SECRET"
echo "---------------------------------------------------"
echo ""

# Save to .env.secrets (not committed)
SECRETS_FILE=".env.secrets"
cat > "$SECRETS_FILE" <<EOF
# Generated JWT Secrets - $(date)
# DO NOT COMMIT THIS FILE
JWT_SECRET=$JWT_SECRET
REFRESH_SECRET=$REFRESH_SECRET
EOF

echo "✅ Secrets saved to $SECRETS_FILE (local backup)"
echo ""

# Check if GCP is available
if command -v gcloud &>/dev/null; then
    echo "GCP Secret Manager available. Add to Secret Manager? (y/N)"
    read -r ADD_TO_GCP

    if [[ "$ADD_TO_GCP" =~ ^[Yy]$ ]]; then
        if [ -z "${GCP_PROJECT_ID:-}" ]; then
            echo "Please enter your GCP Project ID:"
            read -r GCP_PROJECT_ID
            export GCP_PROJECT_ID
        fi

        echo "Adding JWT_SECRET to Secret Manager..."
        echo -n "$JWT_SECRET" | gcloud secrets create jwt-secret \
            --data-file=- \
            --replication-policy="automatic" \
            --project="$GCP_PROJECT_ID" 2>/dev/null || \
        echo -n "$JWT_SECRET" | gcloud secrets versions add jwt-secret \
            --data-file=- \
            --project="$GCP_PROJECT_ID"

        echo "Adding REFRESH_SECRET to Secret Manager..."
        echo -n "$REFRESH_SECRET" | gcloud secrets create refresh-secret \
            --data-file=- \
            --replication-policy="automatic" \
            --project="$GCP_PROJECT_ID" 2>/dev/null || \
        echo -n "$REFRESH_SECRET" | gcloud secrets versions add refresh-secret \
            --data-file=- \
            --project="$GCP_PROJECT_ID"

        echo "✅ Secrets added to GCP Secret Manager"
    fi
fi

echo ""
echo "Next steps:"
echo "1. Open https://github.com/taiyousan15/tepure/settings/secrets/actions"
echo "2. Add JWT_SECRET (copy from above)"
echo "3. Add REFRESH_SECRET (copy from above)"
echo "4. Store $SECRETS_FILE securely (e.g., password manager)"
echo ""
echo "⚠️  Keep $SECRETS_FILE safe - you'll need it for local development"
