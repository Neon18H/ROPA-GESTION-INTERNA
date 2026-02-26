from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class PublicMediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False
    default_acl = None
    querystring_auth = False


class PrivateMediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False
    default_acl = None
    querystring_auth = True


def get_media_storage():
    storage_class = PublicMediaStorage if getattr(settings, 'MEDIA_PUBLIC_READ', True) else PrivateMediaStorage
    return storage_class()
