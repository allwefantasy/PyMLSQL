#!/usr/bin/env bash

instance_type=${1:-"ecs.c5.xlarge"}
## start server
python -m pymlsql.aliyun.dev.start_server \
--image_id "m-bp13ubsorlrxdb9lmv2x" \
--instance_type ${instance_type} \
--keyPairName "mlsql-build-env-local" \
--init_ssh_key false