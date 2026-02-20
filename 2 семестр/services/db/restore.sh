#!/bin/sh
set -e

echo "Restoring database from stroy.backup..."

pg_restore -U "$POSTGRES_USER" \
           -d "$POSTGRES_DB" \
           -c \
           /stroy.backup

echo "Restore finished."
