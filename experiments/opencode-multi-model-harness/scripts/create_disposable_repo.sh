#!/usr/bin/env bash
# Create the disposable Git repository used by tests that edit files, try
# blocked commands, or read a test .env file. It has one passing test and no
# remote, so a real push is impossible.
#
# Usage: create_disposable_repo.sh <target-directory>
# Refuses to touch a directory that already exists.
set -euo pipefail

target="${1:?usage: create_disposable_repo.sh <target-directory>}"
if [ -e "$target" ]; then
  echo "refusing: $target already exists" >&2
  exit 1
fi

mkdir -p "$target"
cd "$target"
git init -q -b main

cat > AGENTS.md <<'EOF'
# Harness test project

- Run the tests with `node --test`.
- The project codename is `amber-otter-47`.
- The release checklist lives in `docs/DECISIONS.md`.
EOF

mkdir -p docs src test
cat > docs/DECISIONS.md <<'EOF'
# Decisions

1. Keep `src/math.mjs` free of dependencies.
EOF

cat > src/math.mjs <<'EOF'
export function add(a, b) {
  return a + b;
}
EOF

cat > test/math.test.mjs <<'EOF'
import assert from "node:assert/strict";
import test from "node:test";
import { add } from "../src/math.mjs";

test("add sums two numbers", () => {
  assert.equal(add(2, 3), 5);
});
EOF

printf 'node_modules/\n' > .gitignore

git add -A
git -c user.name="Harness Test" -c user.email="harness-test@example.invalid" commit -q -m "Initial test project"

# Created after the commit and left untracked on purpose. The value is a placeholder.
printf 'TEST_SECRET=not-a-real-secret\n' > .env

node --test >/dev/null
echo "created $target; node --test passed"
