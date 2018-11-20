#!/usr/bin/env bash

if [ -z "$1" ]; then
  echo " instance_id is required"
  exit 1
fi
## start server
python -m pymlsql.aliyun.dev.stop_release_server  --keyPairName "mlsql-build-env-local" --instance_id $1
