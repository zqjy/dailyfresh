from django.core.files.storage import Storage
from django.conf import settings
from fdfs_client.client import Fdfs_client


class FDFSStorage(Storage):
    """
    fast dfs 文件存储类
    """
    def __init__(self, client_conf=None, base_url=None):
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

        if base_url is None:
            base_url = settings.FDFS_URL
        self.base_url = base_url

    def _open(self, name, mode='rb'):
        """打开文件时使用"""
        pass

    def _save(self, name, content, max_length=None):
        """保存文件时使用"""
        client = Fdfs_client(self.client_conf)
        ret = client.upload_by_buffer(content.read())
        # {
        #     'Group name': 'group1',
        #     'Remote file_id': 'group1\\M00/00/00/wKgfQFyKRleAJN3yAAA3sZPrVzQ7935128',
        #     'Local file name': '',
        #     'Storage IP': '192.168.31.64',
        #     'Status': 'Upload successed.',
        #     'Uploaded size': '13.00KB'
        # }
        if ret.get('Status') != 'Upload successed.':
            # 上传失败
            raise Exception('上传文件到fast dfs失败')

            # 获取返回的文件ID
        filename = ret.get('Remote file_id')

        return filename

    def exists(self, name):
        """django 判断文件名是否可用"""
        return False

    def url(self, name):
        return self.base_url + name