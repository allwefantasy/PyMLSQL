# -*- coding: utf-8 -*-
import logging
import time
from pymlsql.aliyun.ecs_builder import ECSClient, ECSClientBuilder, ECS_STATUS_RUNNING, ECS_STATUS_STOPPED
import pymlsql.aliyun.shellutils as shell

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("InstanceContext")


class ECSInstanceContext(object):

    def __init__(self, instance_id=None, keyPairName="mlsql-build-env", need_public_ip=False):
        self.ecs = None
        self.instance_id = instance_id
        self.public_ip = None
        self.inter_ip = None
        self.keyPairName = keyPairName
        self.need_public_ip = need_public_ip

    def is_ssh_server_ready(self):
        hostname = self.public_ip if self.need_public_ip else self.inter_ip
        try_times = 5
        ready = False
        while try_times > 0:
            try:
                res = shell.ssh_exec_singe_command(ECSClient.home() + "/.ssh/" + self.keyPairName, hostname, "root",
                                                   '"pwd"')
                if res != -1:
                    try_times = 0
                    ready = True
                else:
                    try_times -= 1
                    time.sleep(3)
            except Exception as e:
                logger.exception("cannot connect instance ssh server")
        return ready

    def execute_shell(self, command, execute_user="root"):
        hostname = self.public_ip if self.need_public_ip else self.inter_ip
        return shell.ssh_exec(ECSClient.home() + "/.ssh/" + self.keyPairName, hostname, "root", command, execute_user)

    def copy_from_local(self, remote_username, source, target):
        hostname = self.public_ip if self.need_public_ip else self.inter_ip
        keypath = ECSClient.home() + "/.ssh/" + self.keyPairName
        command = ["scp", "-oStrictHostKeyChecking=no", "-oUserKnownHostsFile=/dev/null", "-i", keypath, "-r", source,
                   remote_username + "@" + hostname + ":" + target]
        print("execute copy command:\n%s" % " ".join(command))
        return shell.run_cmd(command,
                             return_output=True)

    def copy_to_local(self, remote_username, source, target):
        hostname = self.public_ip if self.need_public_ip else self.inter_ip
        keypath = ECSClient.home() + "/.ssh/" + self.keyPairName
        command = ["scp", "-oStrictHostKeyChecking=no", "-oUserKnownHostsFile=/dev/null", "-i", keypath, "-r",
                   remote_username + "@" + hostname + ":" + source,
                   target]
        print("execute copy command:\n%s" % " ".join(command))
        return shell.run_cmd(command,
                             return_output=True)

    def execute_shell_with_hostname_username(self, hostname, username, command):
        return shell.ssh_exec(ECSClient.home() + "/.ssh/" + self.keyPairName, hostname, username, command)

    def start_server(self,
                     instance_type="ecs.ic5.large",
                     image_id="ubuntu_16_0402_64_20G_alibase_20180409.vhd",
                     internet_max_bandwidth_out=1,
                     init_ssh_key=False,
                     timeout=60):

        self.ecs = ECSClientBuilder(). \
            instance_type(instance_type). \
            image_id(image_id). \
            internet_max_bandwidth_out(internet_max_bandwidth_out). \
            key_pair_name(self.keyPairName). \
            build()

        if not self.instance_id:
            if init_ssh_key:
                print(self.ecs.delete_sshkey())
                print(self.ecs.create_sshkey(save_path=ECSClient.home() + "/.ssh"))
                shell.run_cmd(["chmod", "700", ECSClient.home() + "/.ssh/" + self.keyPairName])

            # create temp instance
            self.instance_id = self.ecs.create_after_pay_instance()
            self.ecs.wait_to_stopped_from_pending(self.instance_id, timeout)
            if self.need_public_ip:
                self.public_ip = self.ecs.allocate_public_address(self.instance_id)

            # start instance
            self.ecs.start_instance(instance_id=self.instance_id)

            # show the status
            status = self.ecs.wait_to_running_from_starting(self.instance_id, timeout)
            info = self.ecs.get_instance_detail_by_id(self.instance_id)[0]
            # self.inter_ip = info["InnerIpAddress"]["IpAddress"][0]
            self.inter_ip = info["NetworkInterfaces"]["NetworkInterface"][0]["PrimaryIpAddress"]
            logger.info("start successfully instance_id:%s status:%s" % (self.instance_id, status))
        else:
            logger.info("use instance_id: " + self.instance_id)
            instance_desc = self.ecs.get_instance_detail_by_id(self.instance_id)
            if len(instance_desc) == 0:
                raise ValueError("instance %s is not exist" % self.instance_id)
            status = self.ecs.get_instance_status_by_id(self.instance_id)
            if status != ECS_STATUS_RUNNING and status == ECS_STATUS_STOPPED:
                logger.info("try to start instance_id: " + self.instance_id)
                self.ecs.start_instance(self.instance_id)
                self.ecs.wait_to_running_from_starting(self.instance_id, timeout)
            elif status == ECS_STATUS_RUNNING:
                # do nothing
                logger.info("instance_id: " + self.instance_id + " is running. Do nothing.")
            else:
                logger.warning("instance [%s]'s status is [%s]", self.instance_id, status)
                raise ValueError(
                    "instance [%s]'s status is [%s], is not %s" % (self.instance_id, status, ECS_STATUS_STOPPED))
            self.inter_ip = instance_desc[0]["NetworkInterfaces"]["NetworkInterface"][0]["PrimaryIpAddress"]
            public_addresses = instance_desc[0]["PublicIpAddress"]["IpAddress"]
            if len(public_addresses) > 0:
                self.public_ip = public_addresses[0]
                self.need_public_ip = True

    def close_server(self, timeout=60):
        if not self.ecs:
            self.ecs = ECSClient(self.keyPairName)
        if self.instance_id and self.ecs.check_instance_exists_by_id(self.instance_id):
            self.ecs.stop_instance(self.instance_id)
            self.ecs.wait_to_stopped_from_running(self.instance_id, timeout)
            self.ecs.delete_instance(self.instance_id)
