#!/bin/bash

echo "=== Backend (ruff) ==="
ruff check backend/

echo ""
echo "=== Frontend (eslint) ==="
cd frontend && npm run lint
