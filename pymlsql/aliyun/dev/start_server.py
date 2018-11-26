# -*- coding: utf-8 -*-

import argparse
import logging
import os
from pymlsql.aliyun.dev.instance_context import ECSInstanceContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("build_mysql_server")

parser = argparse.ArgumentParser(description='run shell in new ECS instance.')
parser.add_argument('--instance_id', help='If you already have a instance, please set thi parameter')
parser.add_argument('--image_id', help='image_id', required=True)
parser.add_argument('--keyPairName', help='', required=True)
parser.add_argument('--init_ssh_key', help='', required=True)
parser.add_argument('--instance_type', help='', required=True)
args = parser.parse_args()

# cwd = os.getcwd()
if args.instance_id:
    instance_context = ECSInstanceContext(keyPairName=args.keyPairName, instance_id=args.instance_id,
                                          need_public_ip=True)
else:
    instance_context = ECSInstanceContext(keyPairName=args.keyPairName, need_public_ip=True)

instance_context.start_server(image_id=args.image_id, instance_type=args.instance_type,
                              init_ssh_key=(args.init_ssh_key == "true"))
print("instance_id:" + instance_context.instance_id)
