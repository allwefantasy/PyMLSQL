#!/usr/bin/env bash

## start server
python -m pymlsql.aliyun.dev.start_server --image_id "m-bp16moj3j4180pc2mafn" --keyPairName "mlsql-build-env-local" --init_ssh_key false