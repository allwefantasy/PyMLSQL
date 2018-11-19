#!/usr/bin/env bash

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
    echo "$env must be set to run this script; \n Please run ./mvn_test.sh help to get how to use."
    exit 1
  fi
done

cat << EOF > ${SCRIPT_FILE}
#!/usr/bin/env bash

MLSQL_HTTPS_REPO="https://github.com/allwefantasy/streamingpro.git"
MLSQL_GIT_REPO="git@github.com:allwefantasy/streamingpro.git"

rm -rf streamingpro
git clone \${MLSQL_GIT_REPO} -b ${GIT_BRANCH}
cd streamingpro

BASE_PROFILES="-Pscala-2.11 -Ponline -Phive-thrift-server -Pcarbondata  -Pcrawler -Pautoml"
PUBLISH_SCALA_2_10=0

if [[ "$MLSQL_SPARK_VERSIOIN" > "2.3" ]]; then
  BASE_PROFILES="\$BASE_PROFILES -Pdsl -Pxgboost"
else
  BASE_PROFILES="\$BASE_PROFILES -Pdsl-legacy"
fi

BASE_PROFILES="\$BASE_PROFILES -Pspark-$MLSQL_SPARK_VERSIOIN -Pstreamingpro-spark-$MLSQL_SPARK_VERSIOIN-adaptor"


mvn test -pl streamingpro-mlsql -am \$BASE_PROFILES

EOF






# here we will create a ECS instance dynamically and run the script file
# the remote server.
cat << EOF
execute python command:
        python -m pymlsql.dev.run_remote_shell --script_path ${SCRIPT_FILE}

EOF

python -m pymlsql.dev.run_remote_shell --script_path ${SCRIPT_FILE}


