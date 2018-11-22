#!/usr/bin/env bash

## start server
python -m pymlsql.aliyun.dev.start_server --image_id "m-bp13ubsorlrxdb9lmv2x" --instance_type "ecs.g5.2xlarge" --keyPairName "mlsql-build-env-local" --init_ssh_key false