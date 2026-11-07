#!/bin/bash
# publish.sh - Safe publication pipeline for marsset.github.io
# Enforces mobile phone layout compliance before every publish.

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "======================================================================"
echo " Starting Safe Publication Pipeline (marsset.github.io)"
echo "======================================================================"

# 1. Run Mobile Layout Test with Auto-Fix
echo "[1/3] Running Mobile Phone Layout QA..."
python3 "$REPO_ROOT/scripts/test_mobile_layout.py" --fix

# 2. Check for uncommitted auto-fixes
MODIFIED_POSTS=$(git diff --name-only _posts/ _sass/)
if [ -n "$MODIFIED_POSTS" ]; then
    echo "[!] Auto-fixer repaired mobile layout hazards in:"
    echo "$MODIFIED_POSTS"
    echo "Staging auto-fixed files..."
    git add $MODIFIED_POSTS
fi

# 3. Test Jekyll build
echo "[2/3] Verifying Jekyll build..."
bundle exec jekyll build --trace

# 4. Git status & push confirmation
echo "[3/3] Ready for publish."
git status -s

echo "======================================================================"
echo " Mobile Layout QA & Jekyll Build Passed!"
echo " Proceed with git commit and push."
echo "======================================================================"
