#!/bin/sh
set -e

echo "[decepticon-web] Applying database migrations..."
node node_modules/prisma/build/index.js migrate deploy

echo "[decepticon-web] Starting server..."
exec node server.js
