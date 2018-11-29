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
    echo "===$env must be set to run this script==="
    echo "===Please run ./dev/mvn_test.sh help to get how to use.==="
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
apt-get install wget -y -q
apt-get install gzip -y -q
cd /home/webuser
rm streamingpro.tar.gz
rm -rf streamingpro
rm temp_ServiceFramework.tar.gz
rm -rf temp_ServiceFramework
EOF

instance_id=$1
keyPairName="mlsql-build-env-local"
CONNECT_SERVER_ROOT_PROFILE="--keyPairName ${keyPairName} --execute_user root --instance_id ${instance_id}"
CONNECT_SERVER_WEBUSER_PROFILE="--keyPairName ${keyPairName} --execute_user webuser --instance_id ${instance_id}"

python -m pymlsql.aliyun.dev.run_remote_shell --script_path ${SCRIPT_FILE} \
${CONNECT_SERVER_ROOT_PROFILE}

WORK_DIR="/tmp/${MLSQL_SPARK_VERSIOIN}"
CURRENT_HOME=`pwd`

rm -rf ${WORK_DIR}
mkdir -p ${WORK_DIR}

echo "download ServiceFramework and copy to remote"
cd ${WORK_DIR}
git clone --depth 1 https://github.com/allwefantasy/ServiceFramework.git temp_ServiceFramework
tar czf temp_ServiceFramework.tar.gz temp_ServiceFramework


cd $CURRENT_HOME
python -m pymlsql.aliyun.dev.copy_from_local \
--source ${WORK_DIR}/temp_ServiceFramework.tar.gz \
--target /home/webuser ${CONNECT_SERVER_ROOT_PROFILE}


MLSQL_HTTPS_REPO="https://github.com/allwefantasy/streamingpro.git"
MLSQL_GIT_REPO="git@github.com:allwefantasy/streamingpro.git"

echo "download streamingpro and copy to remote server"
cd ${WORK_DIR}
echo "current branch ${GIT_BRANCH}"

if [[ -z "${LOCAL_MLSQL_PATH}" ]];then
    git clone --depth 1 ${MLSQL_HTTPS_REPO} -b ${GIT_BRANCH}
else
    cp -r ${LOCAL_MLSQL_PATH} .
    cd streamingpro
    if [[ ${GIT_BRANCH} != "master" ]];then
        git fetch origin ${GIT_BRANCH}:${GIT_BRANCH}
        git checkout ${GIT_BRANCH}
    fi
    rm -rf .git
    cd ..
fi

tar czf streamingpro.tar.gz streamingpro

cd $CURRENT_HOME
python -m pymlsql.aliyun.dev.copy_from_local \
--source ${WORK_DIR}/streamingpro.tar.gz \
--target /home/webuser  ${CONNECT_SERVER_ROOT_PROFILE}

echo "grant the resource to webuser"
cat << EOF > ${SCRIPT_FILE}
#!/usr/bin/env bash

cd /home/webuser
chown -R webuser:webuser streamingpro.tar.gz
chown -R webuser:webuser temp_ServiceFramework.tar.gz

EOF

python -m pymlsql.aliyun.dev.run_remote_shell \
--script_path ${SCRIPT_FILE} ${CONNECT_SERVER_ROOT_PROFILE}

echo "unzip the resource"
cat << EOF > ${SCRIPT_FILE}
#!/usr/bin/env bash

source activate mlsql-3.5
cd /home/webuser
tar xf temp_ServiceFramework.tar.gz
tar xf streamingpro.tar.gz
EOF

python -m pymlsql.aliyun.dev.run_remote_shell \
--script_path ${SCRIPT_FILE} ${CONNECT_SERVER_WEBUSER_PROFILE}

echo "mvn install ServiceFramework and test streamingpro"

suites=""
if [ -z ${2} ];then
:
else
suites="-Dsuites=\"*${2}\""
fi


cat << EOF > ${SCRIPT_FILE}
#!/usr/bin/env bash

source activate mlsql-3.5

conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --set show_channel_urls yes
mkdir ~/.pip
echo -e "[global]\ntrusted-host = mirrors.aliyun.com\nindex-url = https://mirrors.aliyun.com/pypi/simple" > ~/.pip/pip.conf

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
export MAVEN_OPTS="-Xmx6000m";mvn clean test -pl streamingpro-mlsql -am \$BASE_PROFILES ${suites}  > sg-test-${MLSQL_SPARK_VERSIOIN}.log
gzip sg-test-${MLSQL_SPARK_VERSIOIN}.log

EOF


python -m pymlsql.aliyun.dev.run_remote_shell \
--script_path ${SCRIPT_FILE} ${CONNECT_SERVER_WEBUSER_PROFILE}

python -m pymlsql.aliyun.dev.copy_to_local \
--source /home/webuser/streamingpro/sg-test-${MLSQL_SPARK_VERSIOIN}.log.gz \
--target . ${CONNECT_SERVER_ROOT_PROFILE}

