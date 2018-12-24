from __future__ import print_function

import sys

import click
from click import UsageError
from pymlsql.aliyun.dev.instance_context import ECSInstanceContext


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


@click.group()
@click.version_option()
def cli():
    pass


@cli.command()
@click.option("--instance-id", "-d", metavar="InstanceId",
              help="", default=None)
@click.option("--image-id", "-i", metavar="ImageId", required=True,
              help="")
@click.option("--instance-type", "-t", metavar="InstanceType", default="ecs.r5.large",
              help="")
@click.option("--key-pair-name", "-k", metavar="keyPairName", required=True, envvar="MLSQL_KEY_PARE_NAME",
              help="")
@click.option("--init-ssh-key", "-s", metavar="initSSHKey", default="true",
              help="")
@click.option("--need-public-ip", "-p", metavar="needPublicIp", default="true",
              help="")
def start(instance_id, image_id, instance_type, key_pair_name, init_ssh_key, need_public_ip):
    try:
        if instance_id:
            instance_context = ECSInstanceContext(keyPairName=key_pair_name, instance_id=instance_id,
                                                  need_public_ip=(need_public_ip == "true"))
        else:
            instance_context = ECSInstanceContext(keyPairName=key_pair_name, need_public_ip=(need_public_ip == "true"))

        instance_context.start_server(image_id=image_id, instance_type=instance_type,
                                      init_ssh_key=(init_ssh_key == "true"))
        print("instance_id:" + instance_context.instance_id)
    except Exception as e:
        eprint("=== %s ===" % e)
        sys.exit(1)


@cli.command()
@click.option("--instance-id", "-d", metavar="InstanceId", required=True,
              help="", default=None)
@click.option("--key-pair-name", "-k", metavar="keyPairName", required=True, envvar="MLSQL_KEY_PARE_NAME",
              help="")
def stop(instance_id, key_pair_name):
    try:
        instance_context = ECSInstanceContext(keyPairName=key_pair_name, instance_id=instance_id,
                                              need_public_ip=False)
        instance_context.close_server()
    except Exception as e:
        eprint("=== %s ===" % e)
        sys.exit(1)


@cli.command()
@click.option("--instance-id", "-d", metavar="InstanceId", required=True,
              help="", default=None)
@click.option("--key-pair-name", "-k", metavar="keyPairName", required=True, envvar="MLSQL_KEY_PARE_NAME",
              help="")
@click.option("--execute-user", "-u", metavar="execute_user", required=True,
              help="")
@click.option("--source", "-s", metavar="source", required=True,
              help="")
@click.option("--target", "-t", metavar="target", required=True,
              help="")
def copy_from_local(instance_id, key_pair_name, execute_user, source, target):
    try:
        instance_context = ECSInstanceContext(keyPairName=key_pair_name, instance_id=instance_id,
                                              need_public_ip=False)
        if instance_context.is_ssh_server_ready():
            instance_context.copy_from_local(execute_user, source, target)
    except Exception as e:
        eprint("=== %s ===" % e)
        sys.exit(1)


@cli.command()
@click.option("--instance-id", "-d", metavar="InstanceId", required=True,
              help="", default=None)
@click.option("--key-pair-name", "-k", metavar="keyPairName", required=True, envvar="MLSQL_KEY_PARE_NAME",
              help="")
@click.option("--execute-user", metavar="execute_user", required=True,
              help="")
@click.option("--source", metavar="source", required=True,
              help="")
@click.option("--target", metavar="target", required=True,
              help="")
def copy_to_local(instance_id, key_pair_name, execute_user, source, target):
    try:
        instance_context = ECSInstanceContext(keyPairName=key_pair_name, instance_id=instance_id,
                                              need_public_ip=False)
        if instance_context.is_ssh_server_ready():
            instance_context.copy_to_local(execute_user, source, target)
    except Exception as e:
        eprint("=== %s ===" % e)
        sys.exit(1)


@cli.command()
@click.option("--instance-id", "-d", metavar="InstanceId", required=True,
              help="", default=None)
@click.option("--key-pair-name", "-k", metavar="keyPairName", required=True, envvar="MLSQL_KEY_PARE_NAME",
              help="")
@click.option("--script-file", metavar="script_file", required=True,
              help="")
@click.option("--execute-user", metavar="execute_user", required=True,
              help="")
@click.option("--need-public-ip", "-p", metavar="needPublicIp", default="true",
              help="")
def exec(instance_id, key_pair_name, script_file, execute_user, need_public_ip):
    try:
        import os
        instance_context = ECSInstanceContext(keyPairName=key_pair_name, instance_id=instance_id,
                                              need_public_ip=(need_public_ip == "true"))

        instance_context.start_server(image_id=None, instance_type=None,
                                      init_ssh_key=False)
        if instance_context.is_ssh_server_ready():
            with open(os.path.abspath(script_file), "r") as script_file:
                content = "\n".join(script_file.readlines())
                res = instance_context.execute_shell(content, execute_user)
                # show the result
                if res != -1:
                    print(res.decode("utf-8"))
    except Exception as e:
        eprint("=== %s ===" % e)
        sys.exit(1)


if __name__ == '__main__':
    cli()
