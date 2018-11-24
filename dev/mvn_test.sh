#!/usr/bin/env bash

#mlsql-build-env
function exit_with_usage {
  cat << EOF
usage: mvn_test
run mvn test with specific branch of StreamingPro
Inputs are specified with the following environment variables:

GIT_BRANCH - Git branch on which to make release
SCRIPT_FILE - the script file you want execute in remote server
MLSQL_SPARK_VERSIOIN - the spark version

EOF
  exit 1
}

set -e
set -o pipefail

if [[ $@ == *"help"* ]]; then
  exit_with_usage
fi

for env in GIT_BRANCH SCRIPT_FILE MLSQL_SPARK_VERSIOIN; do
  if [ -z "${!env}" ]; then
    echo "$env must be set to run this script; \n Please run ./dev/mvn_test.sh help to get how to use."
    exit 1
  fi
done


if [ -z "$1" ]; then
    echo "instance id should be configured"
    exit 1
fi

echo "install git in remote server"
cat << EOF > ${SCRIPT_FILE}
#!/usr/bin/env bash
# apt-get install git -y -q
cd /home/webuser
rm streamingpro.tar.gz
rm -rf streamingpro
rm temp_ServiceFramework.tar.gz
rm -rf temp_ServiceFramework
EOF

python -m pymlsql.aliyun.dev.run_remote_shell --script_path ${SCRIPT_FILE} --keyPairName "mlsql-build-env-local" --execute_user root --instance_id $1

echo "download  ServiceFramework and copy to remote"
rm -rf temp_ServiceFramework
git clone --depth 1 https://github.com/allwefantasy/ServiceFramework.git temp_ServiceFramework
tar czf temp_ServiceFramework.tar.gz temp_ServiceFramework
python -m pymlsql.aliyun.dev.copy_from_local --source temp_ServiceFramework.tar.gz --target /home/webuser --keyPairName "mlsql-build-env-local" --execute_user root --instance_id $1
rm temp_ServiceFramework.tar.gz


MLSQL_HTTPS_REPO="https://github.com/allwefantasy/streamingpro.git"
MLSQL_GIT_REPO="git@github.com:allwefantasy/streamingpro.git"

echo "download streamingpro and copy to remote server"
rm -rf streamingpro
git clone --depth 1 ${MLSQL_HTTPS_REPO} -b ${GIT_BRANCH}
tar czf streamingpro.tar.gz streamingpro
python -m pymlsql.aliyun.dev.copy_from_local --source streamingpro.tar.gz --target /home/webuser --keyPairName "mlsql-build-env-local" --execute_user root --instance_id $1
rm streamingpro.tar.gz

echo "grant the resource to webuser"
cat << EOF > ${SCRIPT_FILE}
#!/usr/bin/env bash

cd /home/webuser
chown -R webuser:webuser streamingpro.tar.gz
chown -R webuser:webuser temp_ServiceFramework.tar.gz

EOF

python -m pymlsql.aliyun.dev.run_remote_shell --script_path ${SCRIPT_FILE} --keyPairName "mlsql-build-env-local" --execute_user root --instance_id $1

echo "unzip the resource"
cat << EOF > ${SCRIPT_FILE}
#!/usr/bin/env bash

source activate mlsql-3.5
cd /home/webuser
tar xf temp_ServiceFramework.tar.gz
tar xf streamingpro.tar.gz
EOF

python -m pymlsql.aliyun.dev.run_remote_shell --script_path ${SCRIPT_FILE} --keyPairName "mlsql-build-env-local" --execute_user webuser --instance_id $1

echo "mvn install ServiceFramework and test streamingpro"

suites=""
if [ -z ${2} ];then
suites="-Dsuites=\"*${2}\""
fi


cat << EOF > ${SCRIPT_FILE}
#!/usr/bin/env bash

source activate mlsql-3.5

cd /home/webuser/temp_ServiceFramework

echo "install ServiceFramework"
mvn install -DskipTests -Pjetty-9 -Pweb-include-jetty-9 > sf.log

cd /home/webuser/streamingpro

BASE_PROFILES="-Pscala-2.11 -Ponline -Phive-thrift-server -Pcarbondata  -Pcrawler"

if [[ "$MLSQL_SPARK_VERSIOIN" > "2.3" ]]; then
  BASE_PROFILES="\$BASE_PROFILES -Pdsl -Pxgboost"
else
  BASE_PROFILES="\$BASE_PROFILES -Pdsl-legacy"
fi

BASE_PROFILES="\$BASE_PROFILES -Pspark-$MLSQL_SPARK_VERSIOIN -Pstreamingpro-spark-$MLSQL_SPARK_VERSIOIN-adaptor"

echo "test streamingpro"
mvn test -pl streamingpro-mlsql -am \$BASE_PROFILES ${suites}  > sg-test.log

EOF


python -m pymlsql.aliyun.dev.run_remote_shell --script_path ${SCRIPT_FILE} --keyPairName "mlsql-build-env-local" --execute_user webuser --instance_id $1

python -m pymlsql.aliyun.dev.copy_to_local --source /home/webuser/streamingpro/sg-test.log --target . --keyPairName "mlsql-build-env-local" --execute_user root --instance_id $1

