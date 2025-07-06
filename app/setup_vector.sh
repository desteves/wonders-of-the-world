#!/bin/bash
set -e

if ! command -v atlas &> /dev/null; then
  echo "err Atlas CLI not found."
  exit 1
fi

echo "127.0.0.1 MDB" >>/etc/hosts
atlas deployments setup MDB --type LOCAL --port 27007 --force

MONGODB_URI='mongodb://localhost:27007/?directConnection=true'
echo "MONGODB_URI=$MONGODB_URI" > .env
exit 0
