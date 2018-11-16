# -*- coding: utf-8 -*-

from pymlsql.aliyun.build_test_server import ECSBuilder

ecs = ECSBuilder(keyPairName="mlsql-build-env")
save_path = ECSBuilder.home() + "/.ssh"
# print(ecs.delete_sshkey())
# print(ecs.create_sshkey(save_path=ECSBuilder.home() + "/.ssh"))

# instanceid = ecs.create_after_pay_instance()
# ecs.wait_to_stopped_from_pending(instanceid, 10)
# ip = ecs.allocate_public_address(instanceid)
# ecs.add_finterprint(save_path, ip)
#
# ecs.start_instance(instance_id=instanceid)
#
# status = ecs.wait_to_running_from_starting(instanceid, 30)
# logger.info("start successfully instance_id:%s status:%s" % (instanceid, status))

instanceid = "i-bp1394635h72uozxj9a6"
ecs.stop_instance(instanceid)
ecs.wait_to_stopped_from_running(instanceid, 30)
ecs.delete_instance(instanceid)
