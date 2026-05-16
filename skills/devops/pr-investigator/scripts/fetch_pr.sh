#!/usr/bin/env bash
# fetch_pr.sh - Fetch PR metadata and diff from GitHub API
# Usage: fetch_pr.sh <pr_url> [github_token]

set -euo pipefail

PR_URL="$1"
TOKEN="${2:-${GITHUB_TOKEN:-}}"

# Parse PR URL to extract owner, repo, number
if [[ "$PR_URL" =~ github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
    OWNER="${BASH_REMATCH[1]}"
    REPO="${BASH_REMATCH[2]}"
    NUMBER="${BASH_REMATCH[3]}"
else
    echo '{"error": "Invalid GitHub PR URL. Expected format: https://github.com/owner/repo/pull/123"}' >&2
    exit 1
fi

# Create output directory
OUTDIR=".hermes/pr-data"
mkdir -p "$OUTDIR"

AUTH_HEADER=""
if [ -n "$TOKEN" ]; then
    AUTH_HEADER="-H Authorization: token $TOKEN"
fi

# Fetch PR metadata
META_FILE="$OUTDIR/pr_${NUMBER}.json"
HTTP_CODE=$(curl -s -o "$META_FILE" -w "%{http_code}" $AUTH_HEADER \
    "https://api.github.com/repos/$OWNER/$REPO/pulls/$NUMBER")

if [ "$HTTP_CODE" != "200" ]; then
    echo "{\"error\": \"GitHub API returned HTTP $HTTP_CODE\"}" >&2
    cat "$META_FILE" >&2
    exit 1
fi

# Fetch diff
DIFF_FILE="$OUTDIR/diff_${NUMBER}.patch"
curl -s $AUTH_HEADER \
    -H "Accept: application/vnd.github.v3.diff" \
    "https://api.github.com/repos/$OWNER/$REPO/pulls/$NUMBER" > "$DIFF_FILE"

# Fetch files changed
FILES_FILE="$OUTDIR/files_${NUMBER}.json"
curl -s $AUTH_HEADER \
    "https://api.github.com/repos/$OWNER/$REPO/pulls/$NUMBER/files?per_page=100" > "$FILES_FILE"

# Output summary
FILES_CHANGED=$(jq '. | length' "$FILES_FILE" 2>/dev/null || echo "0")
ADDITIONS=$(jq '[.[].additions] | add' "$FILES_FILE" 2>/dev/null || echo "0")
DELETIONS=$(jq '[.[].deletions] | add' "$FILES_FILE" 2>/dev/null || echo "0")

echo "{"
echo "  \"pr_number\": $NUMBER,"
echo "  \"owner\": \"$OWNER\","
echo "  \"repo\": \"$REPO\","
echo "  \"metadata_file\": \"$META_FILE\","
echo "  \"diff_file\": \"$DIFF_FILE\","
echo "  \"files_file\": \"$FILES_FILE\","
echo "  \"files_changed\": $FILES_CHANGED,"
echo "  \"additions\": $ADDITIONS,"
echo "  \"deletions\": $DELETIONS"
echo "}"
