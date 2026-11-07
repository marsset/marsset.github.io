#!/bin/bash
# Install git hooks for mobile layout testing

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"

mkdir -p "$HOOKS_DIR"
cp "$REPO_ROOT/scripts/git-hooks/pre-push" "$HOOKS_DIR/pre-push"
chmod +x "$HOOKS_DIR/pre-push"

echo " Git pre-push hook installed successfully to $HOOKS_DIR/pre-push"
