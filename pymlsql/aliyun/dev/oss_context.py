import logging
import oss2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("InstanceContext")


class OssInstance(object):

    def __init__(self, AK, AKS, endpoint="oss-cn-hangzhou-internal.aliyuncs.com"):
        self.AK = AK
        self.AKS = AKS
        self.endpoint = endpoint
        if not self.AK:
            raise ValueError('AK and AKS should be configured')

    def bucket(self, bucket_name):
        auth = oss2.Auth(self.AK, self.AKS)
        return oss2.Bucket(auth, self.endpoint, bucket_name)

    def download(self, bucket_name, target_file_name, save_file_name):
        bucket = self.bucket(bucket_name)
        return bucket.get_object_to_file(target_file_name, save_file_name)

    def upload(self, bucket_name, upload_name, original_file_name):
        bucket = self.bucket(bucket_name)
        return bucket.put_object_from_file(upload_name, original_file_name)
