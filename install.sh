#!/usr/bin/env bash
# install.sh - Install the PR Investigator skill into Hermes Agent
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$SCRIPT_DIR/skills/devops/pr-investigator"
HERMES_SKILLS_DIR="${HERMES_HOME:-$HOME/.hermes}/skills"

echo "🔍 Hermes PR Investigator Installer"
echo "===================================="
echo ""

# Check if Hermes is installed
if ! command -v hermes &> /dev/null; then
    echo "⚠️  Hermes Agent not found in PATH."
    echo "   Please install Hermes first: https://hermes-agent.nousresearch.com/"
    echo ""
    echo "   curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash"
    exit 1
fi

echo "✅ Hermes Agent found"
echo ""

# Create skills directory
mkdir -p "$HERMES_SKILLS_DIR/devops"

# Copy skill
cp -r "$SKILL_DIR" "$HERMES_SKILLS_DIR/devops/pr-investigator"

echo "✅ Skill installed to $HERMES_SKILLS_DIR/devops/pr-investigator"
echo ""

# Make scripts executable
chmod +x "$HERMES_SKILLS_DIR/devops/pr-investigator/scripts/"*.sh
chmod +x "$HERMES_SKILLS_DIR/devops/pr-investigator/scripts/"*.py

echo "✅ Scripts made executable"
echo ""

# Check for GITHUB_TOKEN
if [ -z "${GITHUB_TOKEN:-}" ]; then
    echo "⚠️  GITHUB_TOKEN not set."
    echo "   The skill requires a GitHub token for PR fetching."
    echo "   Create one at: https://github.com/settings/tokens"
    echo "   Then add it to ~/.hermes/.env:"
    echo ""
    echo "   echo 'GITHUB_TOKEN=your_token_here' >> ~/.hermes/.env"
    echo ""
fi

echo "🎉 Installation complete!"
echo ""
echo "Usage:"
echo "  hermes chat --toolsets skills"
echo "  /pr-investigator https://github.com/owner/repo/pull/123"
echo ""
echo "Or start a conversation and ask:"
echo "  'Investigate PR https://github.com/owner/repo/pull/123'"
