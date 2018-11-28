#!/usr/bin/env bash

export SCRIPT_FILE="./k_${MLSQL_SPARK_VERSIOIN}.sh"
start_output=$(./dev/start_server.sh)
echo ----${start_output}-----
instance_id=$(echo ${start_output}|grep '^instance_id:'|cut -d ':' -f2)
echo "fetch instance_id: ${instance_id}"
./dev/mvn_test.sh ${instance_id} ${1:-""}
./dev/stop_server.sh ${instance_id}

