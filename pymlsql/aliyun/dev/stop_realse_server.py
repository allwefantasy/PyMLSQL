# -*- coding: utf-8 -*-

import argparse
import logging
import os
from pymlsql.aliyun.dev.instance_context import ECSInstanceContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("build_mysql_server")

parser = argparse.ArgumentParser(description='run shell in new ECS instance.')
parser.add_argument('--instance_id', help='If you already have a instance, please set this parameter', required=True)
parser.add_argument('--keyPairName', help='', required=True)

args = parser.parse_args()

# cwd = os.getcwd()
instance_context = ECSInstanceContext(keyPairName=args.keyPairName, instance_id=args.instance_id,
                                      need_public_ip=False)
instance_context.close_server()
