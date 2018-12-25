#!/usr/bin/env bash
export MLSQL_KEY_PARE_NAME=mlsql-build-env-local
export MLSQL_TAR="streamingpro-spark_2.3-1.1.6.tar.gz"
export MLSQL_NAME="streamingpro-spark_2.3-1.1.6"
export SCRIPT_FILE="/tmp/k.sh"

set -e
set -o pipefail

echo "Create ECS instance for master"
start_output=$(pymlsql start --image-id m-bp13ubsorlrxdb9lmv2x --need-public-ip true --init-ssh-key false --security-group sg-bp1hi23xfzybp0exjp8a)
echo ----"${start_output}"-----

export instance_id=$(echo "${start_output}"|grep '^instance_id:'|cut -d ':' -f2)
export public_ip=$(echo "${start_output}"|grep '^public_ip:'|cut -d ':' -f2)
export inter_ip=$(echo "${start_output}"|grep '^intern_ip:'|cut -d ':' -f2)

cat << EOF
master instance_id : ${instance_id}
master public_ip : ${public_ip}
master inter_ip : ${inter_ip}
EOF


echo "Fetch master hostname"
cat << EOF > ${SCRIPT_FILE}
#!/usr/bin/env bash
hostname
EOF

export master_hostname=$(pymlsql exec_shell --instance-id ${instance_id} --script-file ${SCRIPT_FILE} --execute-user root)


echo "Start spark master"

cat << EOF > ${SCRIPT_FILE}
#!/usr/bin/env bash
source activate mlsql-3.5
cd /home/webuser/apps/spark-2.3
mkdir -p ~/.ssh
./sbin/start-master.sh -h ${inter_ip}
EOF

pymlsql exec_shell --instance-id ${instance_id} \
--script-file ${SCRIPT_FILE} \
--execute-user webuser


echo "copy ssh file and script to master, so we can create/start slave in master"
pymlsql copy-from-local --instance-id ${instance_id} --execute-user root \
--source /Users/allwefantasy/.ssh/mlsql-build-env-local \
--target /home/webuser/.ssh/


pymlsql copy-from-local --instance-id ${instance_id} --execute-user root \
--source start-slaves.sh \
--target /home/webuser

echo "configure auth of the script"

cat << EOF > ${SCRIPT_FILE}
#!/usr/bin/env bash
chown -R webuser:webuser /home/webuser/start-slaves.sh
chown -R webuser:webuser /home/webuser/.ssh/mlsql-build-env-local
chmod 600 /home/webuser/.ssh/mlsql-build-env-local
chmod u+x /home/webuser/start-slaves.sh
EOF

pymlsql exec_shell --instance-id ${instance_id} \
--script-file ${SCRIPT_FILE} \
--execute-user root

cat << EOF > ${SCRIPT_FILE}
#!/usr/bin/env bash
source activate mlsql-3.5
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --set show_channel_urls yes
mkdir ~/.pip
echo -e "[global]\ntrusted-host = mirrors.aliyun.com\nindex-url = https://mirrors.aliyun.com/pypi/simple" > ~/.pip/pip.conf

if [[ -z "${PyMLSQL_PIP}" ]];then
    git clone https://github.com/allwefantasy/PyMLSQL.git
    cd PyMLSQL
    rm -rf ./dist && pip uninstall -y pymlsql && python setup.py sdist bdist_wheel && cd ./dist/ && pip install pymlsql-1.1.6.2-py2.py3-none-any.whl && cd -
else
    pip install pymlsql
fi

EOF

pymlsql exec_shell --instance-id ${instance_id} \
--script-file ${SCRIPT_FILE} \
--execute-user webuser

echo "run start slave script in master"
cat << EOF > ${SCRIPT_FILE}
#!/usr/bin/env bash
source activate mlsql-3.5
cd /home/webuser

export instance_id=${instance_id}
export public_ip=${public_ip}
export inter_ip=${inter_ip}
export master_hostname=${master_hostname}
export MLSQL_KEY_PARE_NAME=mlsql-build-env-local
export AK=${AK}
export AKS=${AKS}
export SCRIPT_FILE="/tmp/k.sh"

./start-slaves.sh
EOF

pymlsql exec_shell --instance-id ${instance_id} \
--script-file ${SCRIPT_FILE} \
--execute-user webuser


echo "Download MLSQL to master"

cat << EOF > ${SCRIPT_FILE}
#!/usr/bin/env bash
cd /home/webuser

export AK=${AK}
export AKS=${AKS}


pymlsql oss-download --bucket-name mlsql-release-repo --source ${MLSQL_TAR}  --target ${MLSQL_TAR}
tar xf ${MLSQL_TAR}
chown -R webuser:webuser ${MLSQL_NAME}
EOF

pymlsql exec_shell --instance-id ${instance_id} \
--script-file ${SCRIPT_FILE} \
--execute-user root

echo "submit MLSQL"

cat << EOF > ${SCRIPT_FILE}
#!/usr/bin/env bash
source activate mlsql-3.5
cd /home/webuser
cd ${MLSQL_NAME}
export SPARK_HOME=/home/webuser/apps/spark-2.3
export MLSQL_HOME=\`pwd\`
JARS=\$(echo \${MLSQL_HOME}/libs/*.jar | tr ' ' ',')
MAIN_JAR=\$(ls \${MLSQL_HOME}/libs|grep 'streamingpro-mlsql')
echo \$JARS
echo \${MAIN_JAR}
cd \$SPARK_HOME
nohup ./bin/spark-submit --class streaming.core.StreamingApp \
        --jars \${JARS} \
        --master spark://${inter_ip}:7077 \
        --deploy-mode client \
        --name mlsql \
        --conf "spark.kryoserializer.buffer=256k" \
        --conf "spark.kryoserializer.buffer.max=1024m" \
        --conf "spark.serializer=org.apache.spark.serializer.KryoSerializer" \
        --conf "spark.scheduler.mode=FAIR" \
        \${MLSQL_HOME}/libs/\${MAIN_JAR}    \
        -streaming.name mlsql    \
        -streaming.platform spark   \
        -streaming.rest true   \
        -streaming.driver.port 9003   \
        -streaming.spark.service true \
        -streaming.thrift false \
        -streaming.enableHiveSupport false > /dev/null 2>&1 &
EOF

pymlsql exec_shell --instance-id ${instance_id} \
--script-file ${SCRIPT_FILE} \
--execute-user webuser





