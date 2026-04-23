#!/usr/bin/env bash
set -e

echo "Running post-edit checks..."

if [ -d "frontend" ]; then
  cd frontend
  npm run lint || exit 1
  npm run typecheck || exit 1
  cd ..
fi

if [ -d "backend" ]; then
  cd backend
  pytest || exit 1
  cd ..
fi

echo "Post-edit checks passed."