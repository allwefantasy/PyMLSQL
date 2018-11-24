# -*- coding: utf-8 -*-

import argparse
import logging
import os
from pymlsql.aliyun.dev.instance_context import ECSInstanceContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("build_mysql_server")

parser = argparse.ArgumentParser(description='run shell in new ECS instance.')
parser.add_argument('--source', help='the path of script will be executed', required=True)
parser.add_argument('--target', help='the path of script will be executed', required=True)
parser.add_argument('--instance_id', help='If you already have a instance, please set thi parameter', required=True)
parser.add_argument('--execute_user', help='the user will execute the command', required=True)
parser.add_argument('--keyPairName', help='', required=True)

args = parser.parse_args()

print("-----%s %s" % (args.keyPairName, args.instance_id))
# cwd = os.getcwd()
instance_context = ECSInstanceContext(keyPairName=args.keyPairName, instance_id=args.instance_id,
                                      need_public_ip=True)

instance_context.start_server()
try:
    if instance_context.is_ssh_server_ready():
        instance_context.copy_to_local(args.execute_user, args.source, args.target)
except Exception as e:
    logger.exception("Something wrong is happened", exc_info=True)
