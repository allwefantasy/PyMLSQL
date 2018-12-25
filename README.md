## PyMLSQL

PyMLSQL is develop for:

1. PyMLSQL provides python API when you want to develop python machine learning project
in MLSQL.
2. PyMLSQL provides command line to interactive with Aliyun Cloud.

## install PyMLSQL

```
pip install pymlsql
``` 

You can also git clone this project and install manually:

``` shell
# please make sure the x.x.x is replaced by the correct version.
pip uninstall -y pymlsql && python setup.py sdist bdist_wheel &&
cd ./dist/ && pip install pymlsql-x.x.x-py2.py3-none-any.whl && cd -
```

## Aliyun Cloud example:

Make sure AK/AKS are exported in command line.

```shell
# when this is your first time to use create a ecs, please set  init-ssh-key to true
start_out=$(pymlsql start --image-id m-bp13ubsorlrxdb9lmv2x --key-pair-name mlsql-build-env-local --init-ssh-key false)

output:

INFO:ECSClient:using create request from Builder
INFO:ECSClient:{'InstanceId': 'i-bp1atjyfwf1ihqfj1y9c', 'RequestId': '6C721265-1640-43C4-BC06-3F7CEFB52089'}
INFO:ECSClient:instance i-bp1atjyfwf1ihqfj1y9c created task submit successfully.
INFO:ECSClient:[pending -> stopped] [current status: Pending]
INFO:ECSClient:allocate address [121.43.181.27] for [i-bp1atjyfwf1ihqfj1y9c],
INFO:ECSClient:[pending -> stopped] [current status: Starting]
INFO:ECSClient:[starting -> running] [current status: Starting]
INFO:ECSClient:[starting -> running] [current status: Starting]
INFO:ECSClient:[starting -> running] [current status: Starting]
INFO:ECSClient:[starting -> running] [current status: Starting]
INFO:ECSClient:[starting -> running] [current status: Starting]
INFO:ECSClient:[starting -> running] [current status: Starting]
INFO:ECSClient:[starting -> running] [current status: Starting]
INFO:InstanceContext:start successfully instance_id:i-bp1atjyfwf1ihqfj1y9c status:Running
instance_id:i-bp1atjyfwf1ihqfj1y9c

instance_id=$(echo "${start_output}"|grep '^instance_id:'|cut -d ':' -f2)
# you can export MLSQL_KEY_PARE_NAME to avoid configure key-pair-name every time.
pymlsql exec_shell --instance-id ${instance_id}  --key-pair-name mlsql-build-env-local \
--script-file /tmp/k.sh \ 
--execute-user root 

output:

INFO:InstanceContext:use instance_id: i-bp1ek01e6gxvzfbvkrc3
INFO:InstanceContext:instance_id: i-bp1ek01e6gxvzfbvkrc3 is running. Do nothing.
ssh: connect to host 47.110.248.97 port 22: Connection refused
[error] running ssh -oStrictHostKeyChecking=no -oUserKnownHostsFile=/dev/null -i /Users/allwefantasy/.ssh/mlsql-build-env-local root@47.110.248.97 "pwd" ; received return code 255
Warning: Permanently added '47.110.248.97' (ECDSA) to the list of known hosts.
Warning: Permanently added '47.110.248.97' (ECDSA) to the list of known hosts.
Warning: Permanently added '47.110.248.97' (ECDSA) to the list of known hosts.
bin
boot
dev
etc
home
initrd.img
initrd.img.old
lib
lib64
lost+found
media
mnt
opt
proc
root
run
sbin
srv
sys
tmp
usr
var
vmlinuz
vmlinuz.old

## pymlsql also support copy_to_local/copy_from_local command.

## 
pymlsql stop --instance-id ${instance_id}  --key-pair-name mlsql-build-env-local

output:
INFO:ECSClient:[running -> stopped] [current status: Stopping]
INFO:ECSClient:[running -> stopped] [current status: Stopping]
INFO:ECSClient:[running -> stopped] [current status: Stopping]
INFO:ECSClient:wait_to_stopped_from_running success: [Stopped]
INFO:ECSClient:successfully delete instance [i-bp1atjyfwf1ihqfj1y9c]
```


