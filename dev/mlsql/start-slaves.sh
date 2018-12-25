echo "Create instance for slave"
start_output=$(pymlsql start --image-id m-bp13ubsorlrxdb9lmv2x --init-ssh-key false --security-group sg-bp1hi23xfzybp0exjp8a --need-public-ip false)
echo ----"${start_output}"-----
slave_instance_id=$(echo "${start_output}"|grep '^instance_id:'|cut -d ':' -f2)
echo "slave instance id is:${slave_instance_id}"
echo "${slave_instance_id}" >> mlsql.slaves


echo "configure spark slave"

cat << EOF > ${SCRIPT_FILE}
#!/usr/bin/env bash
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