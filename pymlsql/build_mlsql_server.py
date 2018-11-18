# -*- coding: utf-8 -*-

import logging
from pymlsql.aliyun.dev.instance_context import ECSInstanceContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("build_mysql_server")

'''
if you already have a instance , tell ECSInstanceContext the instance_id and
ECSInstanceContext will use it otherwise
will create a new one.
e.g.:

instance_context = ECSInstanceContext(instance_id="i-bp1i989udsn2r21nwi43", keyPairName="mlsql-build-env",
                                      need_public_ip=True)

keyPairName is required however we will create a keyPairName named `mlsql-build-env`
in your ~/.ssh/ by default if you do not provide it.

We use this keyPairName to login ecs instance with ssh.

If you need public ip then set need_public_ip  true(which is False by default), 
ECSInstanceContext will allocate a public ip for your instance, and will use the public ip to connect.
'''
instance_context = ECSInstanceContext(keyPairName="mlsql-build-env",
                                      need_public_ip=True)
try:
    # start server
    instance_context.start_server()
    '''
    Sometimes even the AliYun tell you that the server is running, the ssh server may
    still not be ready, you can use  is_ssh_server_ready to check if the ssh server ready.
    Once it's ready, you can use execute_shell to run script in your instance.
    Notice that we will convert your command to script file ,then transfer it with scp command,
    finally use ssh to execute remotely.
    '''
    if instance_context.is_ssh_server_ready():
        res = instance_context.execute_shell("git clone https://github.com/allwefantasy/PyMLSQL.git .")
        # show the result
        print(res.decode("utf-8"))
except Exception as e:
    logger.exception("Something wrong is happened", exc_info=True)
# close and delete your instance.
instance_context.close_server()
