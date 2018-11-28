export GIT_BRANCH=master

export SCRIPT_FILE="./k_${MLSQL_SPARK_VERSIOIN}.sh"
instance_id=`./dev/start_server.sh`|grep '^instance_id:'|cut -d ':' -f2
./dev/mvn_test.sh ${instance_id}
./dev/stop_server.sh ${instance_id}

