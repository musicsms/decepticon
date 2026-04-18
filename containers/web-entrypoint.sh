#!/bin/sh
set -e

echo "[decepticon-web] Running DB migrations..."
node /app/node_modules/prisma/build/index.js migrate deploy
echo "[decepticon-web] Starting server..."
exec node server.js
