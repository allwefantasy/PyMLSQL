#!/usr/bin/env bash
export MLSQL_KEY_PARE_NAME=mlsql-build-env-local
export MLSQL_RELEASE_DIR="/Users/allwefantasy/CSDNWorkSpace/streamingpro-spark-2.3.x/dev/create-release/"
export MLSQL_TAR="streamingpro-spark_2.3-1.1.6.tar.gz"
export MLSQL_NAME="streamingpro-spark_2.3-1.1.6"
SCRIPT_FILE="/tmp/k.sh"

echo "Create instance for master"
start_output=$(pymlsql start --image-id m-bp13ubsorlrxdb9lmv2x --init-ssh-key false --security-group sg-bp1hi23xfzybp0exjp8a)
echo ----${start_output}-----
instance_id=$(echo ${start_output}|grep '^instance_id:'|cut -d ':' -f2)
public_ip=$(echo ${start_output}|grep '^public_ip:'|cut -d ':' -f2)
inter_ip=$(echo ${start_output}|grep '^intern_ip:'|cut -d ':' -f2)
echo "Master instance id is:${instance_id}"

echo "get master hostname"
cat << EOF > ${SCRIPT_FILE}
#!/usr/bin/env bash
source activate mlsql-3.5
cd /home/webuser/apps/spark-2.3
hostname
EOF

master_hostname=$(pymlsql exec --instance-id ${instance_id} --script-file ${SCRIPT_FILE} --execute-user root)


echo "start spark master"

cat << EOF > ${SCRIPT_FILE}
#!/usr/bin/env bash
source activate mlsql-3.5
cd /home/webuser/apps/spark-2.3
./sbin/start-master.sh -h ${inter_ip}
EOF

pymlsql exec --instance-id ${instance_id} \
--script-file ${SCRIPT_FILE} \
--execute-user webuser


echo "Create instance for slave"
start_output=$(pymlsql start --image-id m-bp13ubsorlrxdb9lmv2x --init-ssh-key false --security-group sg-bp1hi23xfzybp0exjp8a)
echo ----${start_output}-----
slave_instance_id=$(echo ${start_output}|grep '^instance_id:'|cut -d ':' -f2)
echo "slave instance id is:${slave_instance_id}"


echo "configure spark slave"

cat << EOF > ${SCRIPT_FILE}
#!/usr/bin/env bash
source activate mlsql-3.5
echo "${inter_ip} ${master_hostname}" >> /etc/hosts
EOF

pymlsql exec --instance-id ${slave_instance_id} \
--script-file ${SCRIPT_FILE} \
--execute-user root


echo "start spark slave"

cat << EOF > ${SCRIPT_FILE}
#!/usr/bin/env bash
source activate mlsql-3.5
cd /home/webuser/apps/spark-2.3
./sbin/start-slave.sh spark://${inter_ip}:7077
EOF

pymlsql exec --instance-id ${slave_instance_id} \
--script-file ${SCRIPT_FILE} \
--execute-user webuser


echo "Copy MLSQL_TAR to master and extract"
pymlsql copy_from_local --instance-id ${instance_id} --execute-user root \
--source ${MLSQL_RELEASE_DIR}/${MLSQL_TAR} \
--target /home/webuser

cat << EOF > ${SCRIPT_FILE}
#!/usr/bin/env bash

source activate mlsql-3.5

cd /home/webuser
tar xf ${MLSQL_TAR}
chown -R webuser:webuser ${MLSQL_NAME}
EOF

pymlsql exec --instance-id ${instance_id} \
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

pymlsql exec --instance-id ${instance_id} \
--script-file ${SCRIPT_FILE} \
--execute-user webuser





