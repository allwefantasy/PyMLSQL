# -*- coding: utf-8 -*-
import os
import json
import logging
import time
import pymlsql.aliyun.shellutils as shellutils
from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526.AllocatePublicIpAddressRequest import AllocatePublicIpAddressRequest
from aliyunsdkecs.request.v20140526.CreateInstanceRequest import CreateInstanceRequest
from aliyunsdkecs.request.v20140526.DeleteInstanceRequest import DeleteInstanceRequest
from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest
from aliyunsdkecs.request.v20140526.CreateKeyPairRequest import CreateKeyPairRequest
from aliyunsdkecs.request.v20140526.DeleteKeyPairsRequest import DeleteKeyPairsRequest
from aliyunsdkecs.request.v20140526.StartInstanceRequest import StartInstanceRequest
from aliyunsdkecs.request.v20140526.StopInstanceRequest import StopInstanceRequest

ALIYUN_AK = "AK"
ALIYUN_AKS = "AKS"
ALIYUN_REGION = "cn-hangzhou"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ECSClient")

ECS_STATUS_PENDING = "Pending"
ECS_STATUS_RUNNING = "Running"
ECS_STATUS_STOPPED = "Stopped"
ECS_STATUS_STARTING = "Starting"
ECS_STATUS_STOPPING = "Stopping"


class ECSClientBuilder(object):
    def __init__(self):
        self.request = CreateInstanceRequest()
        self.keyPairName = None

    def instance_type(self, value):
        self.request.set_InstanceType(value)
        return self

    def image_id(self, value):
        self.request.set_ImageId(value)
        return self

    def security_group(self, value):
        self.request.set_SecurityGroupId(value)
        return self

    def key_pair_name(self, value):
        self.request.set_KeyPairName(value)
        self.keyPairName = value
        return self

    def internet_max_bandwidth_out(self, value):
        self.request.set_InternetMaxBandwidthOut(value)
        return self

    def build(self):
        if not self.keyPairName:
            raise ValueError("key_pair_name should be set")
        client = ECSClient(self.keyPairName, create_instance_request=self.request)
        return client


class ECSClient(object):

    def __init__(self, keyPairName, create_instance_request=None):
        if not ECSClient.env(ALIYUN_AK) or not ECSClient.env(ALIYUN_AKS):
            raise ValueError("AK or AKS should be configured by environment")
        self.client = AcsClient(
            ECSClient.env(ALIYUN_AK),
            ECSClient.env(ALIYUN_AKS),
            ALIYUN_REGION
        )
        self.create_instance_request = create_instance_request
        self.keyPairName = keyPairName

    @staticmethod
    def env(name):
        return os.environ[name]

    @staticmethod
    def home():
        # return shellutils.run_cmd(["eval", "echo", "~$USER"], True)
        from os.path import expanduser
        return expanduser("~")
        # return "/Users/allwefantasy"
        # from pathlib import Path
        # return str(Path.home())

    # We should create sshkey first then create instance
    def create_sshkey(self, save_path):
        request = CreateKeyPairRequest()
        request.set_KeyPairName(self.keyPairName)
        response = self.execute(request)
        # write private key to ./ssh directory
        with open(save_path + "/" + self.keyPairName, "w") as f:
            f.write(response['PrivateKeyBody'])
        # append fingerprint to known_hosts
        # with open(save_path + "/tmp_knowhost_" + self.keyPairName, "w") as f:
        #     f.write(response['KeyPairFingerPrint'])
        return response

        # We should create sshkey first then create instance

    def add_finterprint(self, save_path, ip):
        pass
        # with open(save_path + "/tmp_knowhost_" + self.keyPairName, 'r') as f:
        #     content = "\n".join(f.readlines())
        # with open(save_path + "/known_hosts", "a") as f:
        #     f.write(ip + " ecdsa-sha2-nistp256 " + content)

    def delete_sshkey(self):
        request = DeleteKeyPairsRequest()
        request.set_KeyPairNames([self.keyPairName])
        response = self.execute(request)
        return response

    def create_after_pay_instance(self, internet_max_bandwidth_out=1, image_id="m-bp19ibpdra8vdltxftbc",
                                  instance_type="ecs.ic5.large"):
        if self.create_instance_request:
            logger.info("using create request from Builder")
            request = self.create_instance_request
        else:
            request = CreateInstanceRequest()
            request.set_ImageId(image_id)
            request.set_InstanceType(instance_type)
            request.set_IoOptimized('optimized')
            request.set_SystemDiskCategory('cloud_ssd')
            request.set_KeyPairName(self.keyPairName)
            if internet_max_bandwidth_out > 0:
                request.set_InternetMaxBandwidthOut(internet_max_bandwidth_out)
        response = self.execute(request)
        logger.info(response)
        instance_id = response.get('InstanceId')
        logger.info("instance %s created task submit successfully.", instance_id)
        return instance_id

    def allocate_public_address(self, instance_id):
        status = self.get_instance_status_by_id(instance_id)
        if status != ECS_STATUS_STOPPED and status != ECS_STATUS_RUNNING:
            logger.warning("instance [%s] is not in [%s],current status [%s], cannot allocate_public_address",
                           instance_id,
                           ",".join([ECS_STATUS_STOPPED, ECS_STATUS_RUNNING]), status)
            return None
        request = AllocatePublicIpAddressRequest()
        request.set_InstanceId(instance_id)
        response = self.execute(request)
        logger.info("allocate address [%s] for [%s],", response["IpAddress"], instance_id)
        return response["IpAddress"]

    def get_instance_detail_by_id(self, instance_id):
        request = DescribeInstancesRequest()
        request.set_InstanceIds(json.dumps([instance_id]))
        response = self.execute(request)
        return response.get('Instances').get('Instance')

    def get_instance_status_by_id(self, instance_id):
        return self.get_instance_detail_by_id(instance_id)[0]["Status"]

    def check_instance_exists_by_id(self, instance_id):
        return len(self.get_instance_detail_by_id(instance_id)) > 0

    def start_instance(self, instance_id):
        status = self.get_instance_status_by_id(instance_id)
        if status != ECS_STATUS_STOPPED:
            logger.warning("instance [%s] is not in [%s],current status [%s], cannot start it", instance_id,
                           ",".join([ECS_STATUS_STOPPED]), status)
            return None
        request = StartInstanceRequest()
        request.set_InstanceId(instance_id)
        response = self.execute(request)
        return response

    def stop_instance(self, instance_id):
        status = self.get_instance_status_by_id(instance_id)
        if status != ECS_STATUS_RUNNING:
            logger.warning("instance [%s] is not in [%s],current status [%s], cannot stop it", instance_id,
                           ",".join([ECS_STATUS_RUNNING]), status)
            return None
        request = StopInstanceRequest()
        request.set_InstanceId(instance_id)
        response = self.execute(request)
        return response

    def delete_instance(self, instance_id, retry=True):
        status = self.get_instance_status_by_id(instance_id)
        if status != ECS_STATUS_STOPPED:
            logger.error("instance [%s] is not in [%s],current status [%s], cannot delete it", instance_id,
                         ",".join([ECS_STATUS_STOPPED]), status)
            return None
        # somethings even it's already ECS_STATUS_STOPPED, we still can not delete it.
        # just sleep 10 seconds
        # we can also retry several times
        time.sleep(10)
        try_times = 5
        while try_times > 0:
            try:
                if not retry:
                    try_times = 0
                request = DeleteInstanceRequest()
                request.set_InstanceId(instance_id)
                request.set_Force(True)
                response = self.execute(request)
                logger.info("successfully delete instance [%s]", instance_id)
                return response
            except Exception as e:
                try_times -= 1
                time.sleep(5)
                logger.exception("cannot delete instance [%s],retry", instance_id)

    @staticmethod
    def pretty_json(item):
        return json.dumps(json.loads(item.decode("utf-8")), indent=4, separators=(',', ': '))

    def show_instances(self):
        request = DescribeInstancesRequest.DescribeInstancesRequest()
        request.set_PageSize(10)
        response = self.client.do_action_with_exception(request)
        return ECSClient.pretty_json(response)

    def wait_to_stopped_from_pending(self, instance_id, timeout=10):
        instances = self.get_instance_detail_by_id(instance_id=instance_id)
        if len(instances) == 0:
            raise ValueError("no instance was found")
        status = instances[0]["Status"]
        time_v = 0
        while status != ECS_STATUS_STOPPED and time_v < timeout:
            time.sleep(5)
            time_v += 5
            logger.info("[pending -> stopped] [current status: %s]", status)
            status = self.get_instance_detail_by_id(instance_id=instance_id)[0]["Status"]
        if time_v >= timeout and status != ECS_STATUS_STOPPED:
            logger.error("fail to wait to be [%s]; current status: [%s]; time_v: [%s]", ECS_STATUS_STOPPED, status,
                         str(time_v))
        return status

    def wait_to_running_from_starting(self, instance_id, timeout=10):
        instances = self.get_instance_detail_by_id(instance_id=instance_id)
        if len(instances) == 0:
            raise ValueError("no instance was found")
        status = instances[0]["Status"]
        logger.info("[pending -> stopped] [current status: %s]", status)
        time_v = 0
        while status != ECS_STATUS_RUNNING and time_v < timeout:
            time.sleep(5)
            time_v += 5
            logger.info("[starting -> running] [current status: %s]", status)
            status = self.get_instance_detail_by_id(instance_id=instance_id)[0]["Status"]

        if time_v >= timeout and status != ECS_STATUS_RUNNING:
            logger.info("fail to wait to be [%s]; current status: [%s]; time_v: [%s]", ECS_STATUS_RUNNING, status,
                        str(time_v))
        return status

    def wait_to_stopped_from_running(self, instance_id, timeout=10):
        instances = self.get_instance_detail_by_id(instance_id=instance_id)
        if len(instances) == 0:
            raise ValueError("no instance was found")
        status = instances[0]["Status"]
        time_v = 0
        while status != ECS_STATUS_STOPPED and time_v < timeout:
            time.sleep(5)
            time_v += 5
            logger.info("[running -> stopped] [current status: %s]", status)
            status = self.get_instance_detail_by_id(instance_id=instance_id)[0]["Status"]
        if time_v >= timeout and status != ECS_STATUS_STOPPED:
            logger.info("fail to wait to be [%s]; current status: [%s]; time_v: [%s]", ECS_STATUS_STOPPED, status,
                        str(time_v))
        if time_v < timeout and status == ECS_STATUS_STOPPED:
            logger.info("wait_to_stopped_from_running success: [%s]", status)
        return status

    def execute(self, request):
        response = self.client.do_action_with_exception(request)
        return json.loads(response.decode("utf-8"))
